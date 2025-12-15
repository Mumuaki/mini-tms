
import pytest
from unittest.mock import Mock, patch
from app.services.gps_service import GpsDozorService

@pytest.fixture
def mock_gps_response():
    return {
        "LastPosition": {
            "Latitude": 48.1486,
            "Longitude": 17.1077,
            "Speed": 0
        }
    }

def test_gps_service_initialization():
    service = GpsDozorService()
    assert service.base_url is not None

@patch('requests.get')
def test_get_vehicle_location(mock_get, mock_gps_response):
    service = GpsDozorService()
    # Configure mock
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_gps_response
    
    # Enable service configuration mock
    with patch.object(GpsDozorService, 'is_configured', return_value=True):
        lat, lng = service.get_vehicle_location("TEST_CODE")
        
        assert lat == 48.1486
        assert lng == 17.1077

def test_get_vehicle_location_not_configured():
    service = GpsDozorService()
    # Force configuration to False
    with patch.object(GpsDozorService, 'is_configured', return_value=False):
        result = service.get_vehicle_location("TEST_CODE")
        assert result is None
