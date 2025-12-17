import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.trans_eu import TransEuScraper

async def main():
    print("=" * 60)
    print("Trans.eu Page Inspector")
    print("=" * 60)
    
    scraper = TransEuScraper()
    
    try:
        # Start browser
        print("\n1. Starting browser...")
        await scraper.start_browser(headless=False)
        print("✓ Browser started")
        
        # Login if needed
        if not scraper.is_logged_in:
            print("\n2. Logging in...")
            await scraper.login()
            print("✓ Logged in")
        
        # Navigate to offers
        print("\n3. Navigating to offers page...")
        await scraper.page.goto(scraper.freights_url, wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(3)
        print("✓ Page loaded")
        
        # Take screenshot
        print("\n4. Taking screenshot...")
        await scraper.page.screenshot(path="page_debug.png", full_page=True)
        print("✓ Screenshot saved to page_debug.png")
        
        # Inspect page structure
        print("\n5. Inspecting page structure...")
        
        # Try to find "Загрузка" text
        print("\n--- Looking for 'Загрузка' label ---")
        labels = await scraper.page.query_selector_all('text="Загрузка"')
        print(f"Found {len(labels)} elements with text 'Загрузка'")
        
        # Get all input fields
        print("\n--- All input fields on page ---")
        inputs = await scraper.page.query_selector_all('input[type="text"]')
        print(f"Found {len(inputs)} text input fields")
        
        for i, inp in enumerate(inputs[:10]):  # Show first 10
            try:
                placeholder = await inp.get_attribute('placeholder')
                name = await inp.get_attribute('name')
                value = await inp.input_value()
                print(f"  Input {i+1}: placeholder='{placeholder}', name='{name}', value='{value}'")
            except:
                pass
        
        # Look for buttons
        print("\n--- Buttons on page ---")
        buttons = await scraper.page.query_selector_all('button')
        print(f"Found {len(buttons)} buttons")
        
        for i, btn in enumerate(buttons[:15]):  # Show first 15
            try:
                text = await btn.text_content()
                if text and text.strip():
                    print(f"  Button {i+1}: '{text.strip()[:50]}'")
            except:
                pass
        
        # Get page HTML structure around filters
        print("\n--- HTML structure (first 5000 chars) ---")
        html = await scraper.page.content()
        # Find section with "Загрузка"
        if "Загрузка" in html:
            idx = html.find("Загрузка")
            snippet = html[max(0, idx-500):idx+1000]
            print(snippet)
        
        print("\n" + "=" * 60)
        print("Inspection complete. Browser will stay open for 60 seconds.")
        print("Check page_debug.png for visual reference.")
        print("=" * 60)
        
        await asyncio.sleep(60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
