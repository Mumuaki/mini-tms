<<<<<<< HEAD
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
=======

import os
import requests
import logging
from typing import Optional, Tuple, List, Dict

logger = logging.getLogger(__name__)

class GpsDozorService:
    def __init__(self):
        self.base_url = os.getenv("GPS_DOZOR_URL", "https://a1.gpsguard.eu/api/v1")
        self.username = os.getenv("GPS_DOZOR_USERNAME")
        self.password = os.getenv("GPS_DOZOR_PASSWORD")
        self.api_key = os.getenv("GPS_DOZOR_API_KEY") # In case they use API Key
        
        # Determine auth method
        self.auth = None
        self.headers = {}
        
        if self.username and self.password:
            self.auth = (self.username, self.password)
        elif self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}" # Assumption
            # Or maybe X-API-Key header?
            
    def is_configured(self) -> bool:
        return bool(self.auth or self.api_key)

    def get_vehicles(self) -> List[Dict]:
        """
        Get list of all vehicles from all groups.
        """
        if not self.is_configured():
            logger.warning("GPS Dozor credentials not set")
            return []
            
        try:
            # First get groups
            groups_url = f"{self.base_url}/groups"
            response = requests.get(groups_url, auth=self.auth, headers=self.headers, timeout=10)
            response.raise_for_status()
            groups = response.json()
            
            all_vehicles = []
            for group in groups:
                group_code = group.get("Code")
                if group_code:
                    v_url = f"{self.base_url}/vehicles/group/{group_code}"
                    v_resp = requests.get(v_url, auth=self.auth, headers=self.headers, timeout=10)
                    if v_resp.status_code == 200:
                        vehicles = v_resp.json()
                        all_vehicles.extend(vehicles)
                        
            return all_vehicles
            
        except Exception as e:
            logger.error(f"Error fetching vehicles from GPS Dozor: {e}")
            return []

    def get_vehicle_location(self, vehicle_id: str) -> Optional[Tuple[float, float]]:
        """
        Get (lat, lng) for a specific vehicle.
        vehicle_id is the 'Code' from the API.
        """
        if not self.is_configured():
            return None
            
        try:
            url = f"{self.base_url}/vehicle/{vehicle_id}"
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            last_pos = data.get("LastPosition")
            if last_pos:
                lat = float(last_pos.get("Latitude", 0))
                lng = float(last_pos.get("Longitude", 0))
                if lat != 0 and lng != 0:
                    return (lat, lng)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching vehicle location: {e}")
            return None
>>>>>>> 97953c3 (Initial commit from Specify template)
