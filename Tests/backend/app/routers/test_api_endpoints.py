
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_launch_browser_endpoint_mocked():
    # We mock the actual browser launch to avoid opening windows during tests
    with patch("app.services.scraper_manager.scraper_manager.launch_browser") as mock_launch:
        mock_launch.return_value = None
        response = client.post("/scraper/launch")
        assert response.status_code == 200
        assert response.json()["success"] is True

def test_freights_list_endpoint():
    response = client.get("/freights")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
