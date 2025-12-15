import logging
import math
from typing import Optional, Dict, List
from ..google_maps import GoogleMapsService
from ..gps_service import GpsDozorService

logger = logging.getLogger(__name__)

class AutomationTools:
    """
    Simple tools for the automation agent to perform calculations and data retrieval.
    """
    
    def __init__(self):
        self.maps_service = GoogleMapsService()
        self.gps_service = GpsDozorService()
        
    def get_my_location(self, vehicle_id: str = None) -> str:
        """
        Get current location of the vehicle from GPS.
        Returns formatted address string or error message.
        """
        if not self.gps_service.is_configured():
            return "Error: GPS Service not configured."
            
        try:
            # If no vehicle_id provided, try to find the first one
            if not vehicle_id:
                vehicles = self.gps_service.get_vehicles()
                if not vehicles:
                    return "Error: No vehicles found in GPS account."
                vehicle_id = vehicles[0].get("Code")
                
            coords = self.gps_service.get_vehicle_location(vehicle_id)
            if not coords:
                return f"Error: Could not get location for vehicle {vehicle_id}"
                
            lat, lng = coords
            
            # Reverse geocode
            addr_data = self.maps_service.reverse_geocode_structured(lat, lng)
            if addr_data and addr_data.get("country_code"):
                cc = addr_data["country_code"]
                zip_code = addr_data.get("postal_code")
                city = addr_data.get("city")
                
                if zip_code:
                    return f"{cc}, {zip_code}"
                elif city:
                    return f"{cc}, {city}"
                else:
                    return f"{cc}"
            
            # Fallback
            address = self.maps_service.reverse_geocode(lat, lng)
            return address if address else f"{lat}, {lng}"
            
        except Exception as e:
            return f"Error getting location: {str(e)}"

    def calculate_distance(self, origin: str, destination: str) -> str:
        """
        Calculate driving distance between two points.
        Returns string with distance in km.
        """
        dist = self.maps_service.calculate_distance(origin, destination)
        if dist is not None:
            return f"{dist} km"
        return "Error: Could not calculate distance."

    def calculate_profit(self, price_eur: float, distance_km: float, cost_per_km: float = 1.0) -> str:
        """
        Calculate profit and rate per km.
        """
        if distance_km <= 0:
            return "Error: Distance must be > 0"
            
        rate = price_eur / distance_km
        cost = distance_km * cost_per_km
        profit = price_eur - cost
        
        return (
            f"Rate: {rate:.2f} EUR/km, "
            f"Cost: {cost:.2f} EUR, "
            f"Profit: {profit:.2f} EUR "
            f"(assuming {cost_per_km} EUR/km cost)"
        )

    def get_tool_definitions(self) -> List[Dict]:
        """
        Returns JSON schema definitions for the tools (for LLM system prompt).
        """
        return [
            {
                "name": "get_my_location",
                "description": "Get current GPS location of the truck.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vehicle_id": {"type": "string", "description": "Optional vehicle ID"}
                    }
                }
            },
            {
                "name": "calculate_distance",
                "description": "Calculate driving distance between two places.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "Start point (e.g. 'Warsaw, PL')"},
                        "destination": {"type": "string", "description": "End point (e.g. 'Berlin, DE')"}
                    },
                    "required": ["origin", "destination"]
                }
            },
            {
                "name": "calculate_profit",
                "description": "Calculate profit and rate per km.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "price_eur": {"type": "number", "description": "Price in EUR"},
                        "distance_km": {"type": "number", "description": "Distance in km"},
                        "cost_per_km": {"type": "number", "description": "Optional cost per km (default 1.0)"}
                    },
                    "required": ["price_eur", "distance_km"]
                }
            }
        ]
