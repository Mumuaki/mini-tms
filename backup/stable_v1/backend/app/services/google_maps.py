import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GoogleMapsService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    def calculate_distance(self, origin: str, destination: str) -> Optional[float]:
        """
        Calculate distance between origin and destination in kilometers.
        Returns None if calculation fails or API key is missing.
        """
        if not self.api_key:
            logger.warning("GOOGLE_MAPS_KEY not set in environment variables")
            return None

        try:
            params = {
                "origins": origin,
                "destinations": destination,
                "key": self.api_key,
                "mode": "driving"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] != "OK":
                logger.error(f"Google Maps API error: {data.get('error_message', data['status'])}")
                return None
                
            # Check if we have results
            if data["rows"] and data["rows"][0]["elements"]:
                element = data["rows"][0]["elements"][0]
                if element["status"] == "OK":
                    # Distance is in meters, convert to km
                    distance_meters = element["distance"]["value"]
                    return round(distance_meters / 1000.0, 2)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return None
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert coordinates to a city name (e.g. 'Warsaw, Poland').
        """
        if not self.api_key:
            return None
            
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "latlng": f"{lat},{lng}",
                "key": self.api_key,
                "language": "en" # Or 'ru'/'pl' depending on preference
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                # Try to find locality and country
                for result in data["results"]:
                    components = result["address_components"]
                    city = None
                    country = None
                    
                    for comp in components:
                        if "locality" in comp["types"]:
                            city = comp["long_name"]
                        elif "country" in comp["types"]:
                            country = comp["long_name"]
                            
                    if city and country:
                        return f"{city}, {country}"
                        
                # Fallback to formatted address of the first result
                return data["results"][0]["formatted_address"]
                
            return None
            
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {e}")
            return None

    def reverse_geocode_structured(self, lat: float, lng: float) -> Optional[dict]:
        """
        Return structured address data: {'country_code': 'SK', 'postal_code': '82106', 'city': 'Bratislava'}
        """
        if not self.api_key:
            return None
            
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "latlng": f"{lat},{lng}",
                "key": self.api_key,
                "language": "en"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                result = data["results"][0]
                components = result["address_components"]
                
                res = {
                    "country_code": None,
                    "postal_code": None,
                    "city": None
                }
                
                for comp in components:
                    types = comp["types"]
                    if "country" in types:
                        res["country_code"] = comp["short_name"]
                    elif "postal_code" in types:
                        res["postal_code"] = comp["long_name"].replace(" ", "")
                    elif "locality" in types:
                        res["city"] = comp["long_name"]
                    elif "administrative_area_level_1" in types and not res["city"]:
                         res["city"] = comp["long_name"]
                
                return res
                
            return None
            
        except Exception as e:
            logger.error(f"Error in structured reverse geocoding: {e}")
            return None
