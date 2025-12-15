import asyncio
import re
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import models, database
from .trans_eu import TransEuScraper
from .google_maps import GoogleMapsService
from .scraper_manager import scraper_manager
from .gps_service import GpsDozorService

# --- Helpers ---

def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Преобразует строку даты (DD.MM.YYYY) в объект datetime."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        return None

def _parse_price(price_str: Optional[str]) -> Optional[float]:
    """Извлекает числовое значение цены из строки."""
    if not price_str:
        return None
    try:
        numbers = re.findall(r'\d+[.,]?\d*', price_str)
        if numbers:
            return float(numbers[0].replace(',', '.'))
    except Exception:
        pass
    return None

def _resolve_origin(origin_input: str, gps_service: GpsDozorService, maps_service: GoogleMapsService) -> str:
    """
    Определяет точку загрузки. Если не задана вручную, пытается получить через GPS.
    """
    if origin_input:
        return origin_input

    if not gps_service.is_configured():
        return ""

    print("Origin not provided. Attempting to fetch from GPS Dozor...")
    try:
        vehicles = gps_service.get_vehicles()
        if not vehicles:
            print("No vehicles found in GPS Dozor account.")
            return ""

        # TODO: Allow user to select vehicle in settings. Currently picking first.
        vehicle = vehicles[0]
        v_code = vehicle.get("Code")
        print(f"Tracking vehicle: {vehicle.get('Name')} ({v_code})")
        
        coords = gps_service.get_vehicle_location(v_code)
        if not coords:
            print("Could not get vehicle location.")
            return ""

        lat, lng = coords
        print(f"Vehicle location: {lat}, {lng}")
        
        # Structured Geocoding
        addr_data = maps_service.reverse_geocode_structured(lat, lng)
        if addr_data and addr_data.get("country_code"):
            cc = addr_data["country_code"]
            zip_code = addr_data.get("postal_code")
            city = addr_data.get("city")
            
            origin = f"{cc}, {zip_code}" if zip_code else f"{cc}, {city}" if city else cc
            print(f"Formatted origin from GPS: {origin}")
            return origin
        else:
            # Fallback
            address = maps_service.reverse_geocode(lat, lng)
            if address:
                print(f"Reverse geocoded address (fallback): {address}")
                return address

    except Exception as e:
        print(f"Error fetching GPS location: {e}")
    
    return ""

def _calculate_rates(distance_km: Optional[int]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Расчет ставок (min, avg, max) на основе дистанции."""
    if not distance_km:
        return None, None, None
    return (
        round(distance_km * 1.2, 2),
        round(distance_km * 1.4, 2),
        round(distance_km * 1.6, 2)
    )

def _save_freights_to_db(freights_data: List[Dict], db: Session, maps_service: GoogleMapsService) -> int:
    """Сохранение списка грузов в базу данных."""
    new_count = 0
    for data in freights_data:
        try:
            # Parse simple fields
            loading_date = _parse_date(data.get("loading_date"))
            unloading_date = _parse_date(data.get("unloading_date"))
            price = _parse_price(data.get("price_original"))
            loading_place = data.get("loading_place")
            unloading_place = data.get("unloading_place")

            # Calculate Distance & Rates
            distance_km = None
            if loading_place and unloading_place:
                distance_km = maps_service.calculate_distance(loading_place, unloading_place)
            
            rate_min, rate_avg, rate_max = _calculate_rates(distance_km)

            # Create Record
            freight = models.Freight(
                trans_id=data["trans_id"],
                loading_place=loading_place,
                unloading_place=unloading_place,
                loading_date=loading_date,
                unloading_date=unloading_date,
                cargo_info=data.get("cargo_info"),
                price_original=price,
                currency=data.get("currency", "EUR"),
                distance_km=distance_km,
                rate_min=rate_min,
                rate_avg=rate_avg,
                rate_max=rate_max,
                # Additional fields from detailed parsing
                body_type=data.get("body_type"),
                capacity=data.get("capacity"),
                ldm=data.get("ldm"),
                payment_terms=data.get("payment_terms"),
                additional_description=data.get("additional_description")
            )

            db.add(freight)
            db.commit()
            new_count += 1

        except IntegrityError:
            db.rollback()
            continue
        except Exception as e:
            print(f"Error saving freight {data.get('trans_id')}: {e}")
            db.rollback()
            continue
            
    return new_count

# --- Main Task ---

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
    
    # 1. Get Browser Page
    page = await scraper_manager.get_page()
    if not page:
        print("ERROR: Browser not launched. User must click 'Open Browser' first!")
        return
    
    # Check simple connectivity before complex logic
    try:
        if "platform.trans.eu" not in page.url and "about:blank" not in page.url:
             print(f"Current page is {page.url}, might need navigation.")
    except: pass

    # 2. Init Services
    maps_service = GoogleMapsService()
    gps_service = GpsDozorService()
    db = database.SessionLocal()
    
    try:
        # 3. Resolve Origin (Manual or GPS)
        final_origin = _resolve_origin(origin, gps_service, maps_service)
        
        # 4. Prepare Filters
        filters = {}
        if final_origin: filters["origin"] = final_origin
        if destination: filters["destination"] = destination
        if loading_date_from: filters["loading_date_from"] = loading_date_from
        if loading_date_to: filters["loading_date_to"] = loading_date_to
        if unloading_date_from: filters["unloading_date_from"] = unloading_date_from
        if unloading_date_to: filters["unloading_date_to"] = unloading_date_to
        
        print("=" * 60)
        print("FILTERS CONFIGURATION:")
        for k, v in filters.items():
            print(f"  {k}: {v}")
        print("=" * 60)

        # 5. Run Scraper
        # We instantiate Scraper with the existing page
        scraper = TransEuScraper(page=page)
        
        # NOTE: Logic inside search_freights handles navigation and waiting
        freights_data = await scraper.search_freights(filters)
        
        print(f"Scraper finished. Found {len(freights_data)} items.")
        
        # 6. Save to DB
        saved_count = _save_freights_to_db(freights_data, db, maps_service)
        print(f"Task finished. Successfully saved {saved_count} new freights.")
        
    except Exception as e:
        print(f"Critical Scraper Task Error: {e}")
        traceback.print_exc()
    
    finally:
        db.close()


async def launch_browser_task() -> bool:
    """Helper used by tests to launch the browser via scraper_manager.

    Returns True on success, False on failure.
    """
    try:
        await scraper_manager.launch_browser()
        return True
    except Exception as e:
        print(f"launch_browser_task failed: {e}")
        return False
