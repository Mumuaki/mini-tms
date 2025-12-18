import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.tasks import run_scraper_task

async def main():
    print("Running scraper task manually...")
    # Run with headless=False to see what happens
    await run_scraper_task(origin="Polska", destination="Niemcy", headless=False)

if __name__ == "__main__":
    asyncio.run(main())
