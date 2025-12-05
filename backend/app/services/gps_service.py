import httpx
import logging
from datetime import datetime
from app.models import Truck, VehicleLocation
from app.services.google_maps import GoogleMapsService
from app.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

class GPSService:
    def __init__(self):
        self.base_url = settings.GPS_DOZOR_API_URL
        self.username = settings.GPS_DOZOR_USERNAME
        self.password = settings.GPS_DOZOR_PASSWORD
        self.maps_service = GoogleMapsService()
    
    async def get_vehicle_location(self, vehicle_code: str) -> dict:
        """Get vehicle coordinates from GPS Dozor API"""
        async with httpx.AsyncClient(auth=(self.username, self.password)) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/vehicle/location",
                    params={"code": vehicle_code},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "lat": float(data.get("latitude")),
                    "lon": float(data.get("longitude")),
                    "speed": float(data.get("speed", 0)),
                    "timestamp": data.get("timestamp"),
                    "accuracy": float(data.get("accuracy", 0)),
                }
            except httpx.HTTPError as e:
                logger.error(f"❌ GPS Dozor API error: {e}")
                raise
    
    async def reverse_geocode_structured(self, lat: float, lon: float) -> dict:
        """Convert coordinates to address using Google Maps"""
        return await self.maps_service.reverse_geocode(lat, lon)
    
    async def update_truck_location(self, truck: Truck, db) -> None:
        """Update truck location from GPS Dozor and geocode it"""
        try:
            # Get GPS coordinates
            gps_d
