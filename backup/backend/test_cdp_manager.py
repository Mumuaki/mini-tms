import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.scraper_manager import scraper_manager

async def main():
    print("Testing CDP-based scraper_manager...")
    try:
        print("Launching browser...")
        await scraper_manager.launch_browser()
        print("✓ Browser launched!")
        
        page = await scraper_manager.get_page()
        if page:
            print(f"✓ Page URL: {page.url}")
            print("Browser should be visible. Press Ctrl+C to stop.")
            await asyncio.sleep(300)
        else:
            print("ERROR: No page available")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
