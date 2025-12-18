import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add the current directory to sys.path to make 'app' importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.tasks import run_scraper_task

async def main():
    parser = argparse.ArgumentParser(description="Run Trans.eu scraper task")
    
    parser.add_argument("--origin", "-o", help="Origin location (e.g. 'PL, 00-001')")
    parser.add_argument("--destination", "-d", help="Destination location")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    # Date arguments
    parser.add_argument("--load-from", help="Loading date from (DD.MM.YYYY)")
    parser.add_argument("--load-to", help="Loading date to (DD.MM.YYYY)")
    parser.add_argument("--unload-from", help="Unloading date from (DD.MM.YYYY)")
    parser.add_argument("--unload-to", help="Unloading date to (DD.MM.YYYY)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Starting Scraper CLI")
    print("=" * 60)
    
    # If origin is not provided, the task will try to use GPS
    if not args.origin:
        print("No origin provided. The task will attempt to use GPS location.")
        
    await run_scraper_task(
        origin=args.origin,
        destination=args.destination,
        headless=args.headless,
        loading_date_from=args.load_from,
        loading_date_to=args.load_to,
        unloading_date_from=args.unload_from,
        unloading_date_to=args.unload_to
    )

if __name__ == "__main__":
    # Fix for Windows asyncio loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScraper stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
