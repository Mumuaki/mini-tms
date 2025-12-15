import requests

print("Testing /scraper/launch endpoint...")
try:
    response = requests.post("http://localhost:8000/scraper/launch", timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"ERROR: {e}")
