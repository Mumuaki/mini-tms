from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/minitms"
    
    # API
    API_TITLE: str = "Mini-TMS"
    DEBUG: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    
    # GPS Dozor
    GPS_DOZOR_USERNAME: str
    GPS_DOZOR_PASSWORD: str
    GPS_DOZOR_API_URL: str = "https://a1.gpsguard.eu/api/v1"
    
    # Google Maps
    GOOGLE_MAPS_API_KEY: str
    
    # OpenAI (for Agentic Automation)
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    # Playwright
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT: int = 30000  # ms
    
    # Trans.eu
    TRANSEU_PLATFORM_URL: str = "https://platform.trans.eu/exchange/offers"
    
    class Config:
        env_file = ".env"
