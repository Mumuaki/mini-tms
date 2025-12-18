import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.scraper_manager import scraper_manager

async def main():
    print("Testing new scraper_manager...")
    try:
        await scraper_manager.launch_browser()
        print("✓ Browser launched successfully!")
        print("Browser should be visible now. Press Ctrl+C to stop.")
        # Keep running
        await asyncio.sleep(300)  # 5 minutes
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
