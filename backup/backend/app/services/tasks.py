import asyncio
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from .. import models, database
from .trans_eu import TransEuScraper
from .google_maps import GoogleMapsService
from .scraper_manager import scraper_manager
from .gps_service import GpsDozorService

async def run_scraper_task(
    origin: str, 
    destination: str, 
    headless: bool,
    loading_date_from: str = None,
    loading_date_to: str = None,
    unloading_date_from: str = None,
    unloading_date_to: str = None
):
    """
    Background task to run the scraper using the open browser.
    """
    print(f"Starting scraper task: {origin} -> {destination}")
    
    # Get the page from singleton manager
    page = await scraper_manager.get_page()
    
    if not page:
        print("ERROR: Browser not launched. User must click 'Open Browser' first!")
        return
    
    maps_service = GoogleMapsService()
    gps_service = GpsDozorService()
    db = database.SessionLocal()
    
    try:

        # Check if we're on the right page
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        # Navigate to offers page if not there
        if "exchange/offers" not in current_url:
            print("Navigating to offers page...")
            await page.goto("https://platform.trans.eu/exchange/offers", wait_until="domcontentloaded", timeout=60_000)
            await asyncio.sleep(2)
        
        # Initialize Scraper with existing page
        scraper = TransEuScraper()
        scraper.page = page
        scraper.is_logged_in = True
        
        # GPS Integration: If origin is empty, try to get from GPS
        if not origin and gps_service.is_configured():
            print("Origin not provided. Attempting to fetch from GPS Dozor...")
            try:
                vehicles = gps_service.get_vehicles()
                if vehicles:
                    # Pick the first one for now
                    # TODO: Allow user to select vehicle in settings
                    vehicle = vehicles[0]
                    v_code = vehicle.get("Code")
                    print(f"Tracking vehicle: {vehicle.get('Name')} ({v_code})")
                    
                    coords = gps_service.get_vehicle_location(v_code)
                    if coords:
                        lat, lng = coords
                        print(f"Vehicle location: {lat}, {lng}")
                        
                        # Use structured reverse geocoding
                        addr_data = maps_service.reverse_geocode_structured(lat, lng)
                        if addr_data and addr_data.get("country_code"):
                            # Format: CC, Zip (e.g. SK, 82106) or CC, City
                            cc = addr_data["country_code"]
                            zip_code = addr_data.get("postal_code")
                            city = addr_data.get("city")
                            
                            if zip_code:
                                origin = f"{cc}, {zip_code}"
                            elif city:
                                origin = f"{cc}, {city}"
                            else:
                                origin = f"{cc}"
                                
                            print(f"Formatted origin from GPS: {origin}")
                        else:
                            # Fallback to simple address
                            address = maps_service.reverse_geocode(lat, lng)
                            if address:
                                origin = address
                                print(f"Reverse geocoded address (fallback): {address}")
                            else:
                                print("Could not reverse geocode location.")
                    else:
                        print("Could not get vehicle location.")
                else:
                    print("No vehicles found in GPS Dozor account.")
            except Exception as e:
                print(f"Error fetching GPS location: {e}")
        
        # Apply filters
        filters = {}
        if origin:
            filters["origin"] = origin
        if destination:
            filters["destination"] = destination
        
        # Add dates
        if loading_date_from:
            filters["loading_date_from"] = loading_date_from
        if loading_date_to:
            filters["loading_date_to"] = loading_date_to
        if unloading_date_from:
            filters["unloading_date_from"] = unloading_date_from
        if unloading_date_to:
            filters["unloading_date_to"] = unloading_date_to
            
        print("=" * 60)
        print("FILTERS TO APPLY:")
        print(f"  Origin: {filters.get('origin', 'NOT SET')}")
        print(f"  Destination: {filters.get('destination', 'NOT SET')}")
        print(f"  Loading Date From: {filters.get('loading_date_from', 'NOT SET')}")
        print(f"  Loading Date To: {filters.get('loading_date_to', 'NOT SET')}")
        print(f"  Unloading Date From: {filters.get('unloading_date_from', 'NOT SET')}")
        print(f"  Unloading Date To: {filters.get('unloading_date_to', 'NOT SET')}")
        print("=" * 60)
            
        if filters:
            print(f"Applying filters via TransEuScraper: {filters}")
            await scraper._apply_filters(filters)
        
        # Parse freight list
        print("Parsing freight list...")
        freights_data = await scraper._parse_freight_list()
        
        print(f"Scraper found {len(freights_data)} freights")
        
        # Save to database
        new_count = 0
        for freight_data in freights_data:
            try:
                # Parse dates
                loading_date = None
                unloading_date = None
                try:
                    if freight_data.get("loading_date"):
                        loading_date = datetime.strptime(freight_data["loading_date"], "%d.%m.%Y")
                except:
                    pass
                
                try:
                    if freight_data.get("unloading_date"):
                        unloading_date = datetime.strptime(freight_data["unloading_date"], "%d.%m.%Y")
                except:
                    pass
                
                # Parse price
                price = None
                try:
                    price_str = freight_data.get("price_original", "")
                    if price_str:
                        import re
                        numbers = re.findall(r'\d+[.,]?\d*', price_str)
                        if numbers:
                            price = float(numbers[0].replace(',', '.'))
                except:
                    pass
                
                # Calculate distance
                distance_km = None
                if freight_data.get("loading_place") and freight_data.get("unloading_place"):
                    distance_km = maps_service.calculate_distance(
                        freight_data["loading_place"],
                        freight_data["unloading_place"]
                    )
                
                # Calculate rates
                rate_min = None
                rate_avg = None
                rate_max = None
                
                if distance_km:
                    rate_min = round(distance_km * 1.2, 2)
                    rate_avg = round(distance_km * 1.4, 2)
                    rate_max = round(distance_km * 1.6, 2)
                
                # Create freight object
                freight = models.Freight(
                    trans_id=freight_data["trans_id"],
                    loading_place=freight_data.get("loading_place"),
                    unloading_place=freight_data.get("unloading_place"),
                    loading_date=loading_date,
                    unloading_date=unloading_date,
                    cargo_info=freight_data.get("cargo_info"),
                    price_original=price,
                    currency=freight_data.get("currency", "EUR"),
                    distance_km=distance_km,
                    rate_min=rate_min,
                    rate_avg=rate_avg,
                    rate_max=rate_max
                )
                
                db.add(freight)
                db.commit()
                new_count += 1
                
            except IntegrityError:
                db.rollback()
                continue
            except Exception as e:
                print(f"Error saving freight: {e}")
                db.rollback()
                continue
                
        print(f"Task finished. Saved {new_count} new freights.")
        
    except Exception as e:
        print(f"Scraper task failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # ВАЖНО: Браузер НЕ закрывается! Только пользователь может его закрыть.
        db.close()
