import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.trans_eu import TransEuScraper

async def main():
    parser = argparse.ArgumentParser(description="Run Playwright-based Trans.eu Automation")
    parser.add_argument("--origin", "-o", default="SK, 93101", help="Origin location (e.g., SK, 93101)")
    parser.add_argument("--destination", "-d", default="DE, 10115", help="Destination location")
    parser.add_argument("--loading-date-from", default=None, help="Loading date from (DD.MM.YYYY)")
    parser.add_argument("--loading-date-to", default=None, help="Loading date to (DD.MM.YYYY)")
    
    args = parser.parse_args()

    # Default dates if not provided
    if not args.loading_date_from:
        args.loading_date_from = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    if not args.loading_date_to:
        args.loading_date_to = (datetime.now() + timedelta(days=2)).strftime("%d.%m.%Y")

    print("=" * 60)
    print(f"PLAYWRIGHT AUTOMATION")
    print(f"Origin: {args.origin}")
    print(f"Destination: {args.destination}")
    print(f"Loading Date: {args.loading_date_from} - {args.loading_date_to}")
    print("=" * 60)

    # Get credentials from env
    username = os.getenv("TRANS_EU_USERNAME")
    password = os.getenv("TRANS_EU_PASSWORD")
    
    if not username or not password:
        print("❌ ERROR: TRANS_EU_USERNAME and TRANS_EU_PASSWORD must be set in .env")
        return

    scraper = TransEuScraper(username, password, headless=False)
    
    try:
        print("\n[1] Logging in...")
        await scraper.login()
        print("✓ Logged in successfully")
        
        print("\n[2] Applying filters...")
        filters = {
            "origin": args.origin,
            "destination": args.destination,
            "loading_date_from": args.loading_date_from,
            "loading_date_to": args.loading_date_to
        }
        
        await scraper._apply_filters(filters)
        print("✓ Filters applied")
        
        print("\n[3] Parsing results...")
        freights = await scraper._parse_freight_list()
        
        print(f"\n✅ Found {len(freights)} freights:")
        for i, freight in enumerate(freights[:5], 1):  # Show first 5
            print(f"   [{i}] {freight.get('route', 'N/A')} - {freight.get('price', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("Automation completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
