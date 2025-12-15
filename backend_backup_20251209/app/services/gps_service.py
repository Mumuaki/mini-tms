
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
