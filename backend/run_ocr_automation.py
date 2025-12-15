import asyncio
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.automation import AsyncAgentObserver, AsyncPyautoguiActionHandler, AsyncScreenshotMaker
from app.services.automation.ocr_helper import OCRHelper

async def main():
    parser = argparse.ArgumentParser(description="Run Trans.eu with OCR-assisted automation")
    parser.add_argument("--origin", "-o", default="Warszawa", help="Origin location")
    parser.add_argument("--destination", "-d", default="Berlin", help="Destination location")
    
    args = parser.parse_args()

    print("=" * 60)
    print(f"Trans.eu OCR-Assisted Automation")
    print(f"Task: {args.origin} -> {args.destination}")
    print("=" * 60)

    observer = AsyncAgentObserver()
    observer.set_agent_name("OCR-Bot")
    
    handler = AsyncPyautoguiActionHandler()
    screenshot_maker = AsyncScreenshotMaker(save_history=True)
    ocr = OCRHelper()
    
    try:
        print("\nWARNING: Make sure Trans.eu is open and you're logged in!")
        print("Starting in 5 seconds...")
        await asyncio.sleep(5)
        
        # Step 1: Find loading location field (search for "Все страны" or existing location)
        await observer.observe_step("Looking for loading location field", status="info")
        print("\n[1] Searching for loading location field...")
        
        screenshot = await screenshot_maker.take_screenshot(save_tag="step1_find_loading")
        
        # Try multiple search terms
        search_terms = ["Все страны", "SK,", "PL,", "DE,", "CZ,"]  # Common country codes
        coords = None
        
        for term in search_terms:
            coords = await ocr.find_text_on_screen(term, screenshot)
            if coords:
                print(f"Found '{term}' - this is likely the loading location button")
                break
        
        if not coords:
            # Fallback: search for the first visible button in the filter area
            print("Trying to find any location button...")
            all_text = await ocr.find_all_text_on_screen(screenshot)
            # Filter for short texts that might be country codes
            for item in all_text:
                text = item['text'].strip()
                if len(text) <= 15 and (',' in text or text == "Все страны"):
                    coords = (item['x'], item['y'])
                    print(f"Found potential location field: '{text}'")
                    break
        
        if coords:
            x, y = coords
            print(f"Clicking loading location field at ({x}, {y})")
            await handler.click(x, y)
            await asyncio.sleep(1.5)
            
            await observer.observe_step(
                "Clicked loading location field",
                details={"coords": f"({x}, {y})"},
                screenshot=screenshot,
                status="success"
            )
            
            # Step 2: Clear existing value and type origin
            print(f"\n[2] Clearing field and typing '{args.origin}'...")
            # Select all and delete
            await handler.hotkey("ctrl", "a")
            await asyncio.sleep(0.3)
            await handler.press_key("delete")
            await asyncio.sleep(0.5)
            
            # Type new value
            await handler.type_text(args.origin)
            await asyncio.sleep(2)
            
            await observer.observe_step(f"Typed '{args.origin}'", status="success")
            
            # Step 3: Wait for dropdown and press Enter or Down+Enter
            print("\n[3] Selecting first suggestion...")
            await asyncio.sleep(1)
            await handler.press_key("down")  # Select first option
            await asyncio.sleep(0.5)
            await handler.press_key("enter")
            await asyncio.sleep(2)
            
            await observer.observe_step("Selected loading location", status="success")
            
        else:
            print("ERROR: Could not find loading location field")
            await observer.observe_step("Failed to find loading location field", status="failed")
            return
            
        # Step 4: Find unloading location field (second location button)
        await observer.observe_step("Looking for unloading location field", status="info")
        print("\n[4] Searching for unloading location field...")
        
        screenshot = await screenshot_maker.take_screenshot(save_tag="step4_find_unloading")
        all_text = await ocr.find_all_text_on_screen(screenshot)
        
        # Find all potential location buttons and take the second one
        location_buttons = []
        for item in all_text:
            text = item['text'].strip()
            if len(text) <= 15 and (',' in text or text == "Все страны"):
                location_buttons.append(item)
        
        if len(location_buttons) >= 2:
            # Second button is unloading location
            second_button = location_buttons[1]
            x, y = second_button['x'], second_button['y']
            print(f"Found unloading location field at ({x}, {y})")
            await handler.click(x, y)
            await asyncio.sleep(1.5)
            
            await observer.observe_step(
                "Clicked unloading location field",
                details={"coords": f"({x}, {y})"},
                screenshot=screenshot,
                status="success"
            )
            
            # Step 5: Clear and type destination
            print(f"\n[5] Clearing field and typing '{args.destination}'...")
            await handler.hotkey("ctrl", "a")
            await asyncio.sleep(0.3)
            await handler.press_key("delete")
            await asyncio.sleep(0.5)
            
            await handler.type_text(args.destination)
            await asyncio.sleep(2)
            
            await observer.observe_step(f"Typed '{args.destination}'", status="success")
            
            # Step 6: Select suggestion
            print("\n[6] Selecting first suggestion...")
            await asyncio.sleep(1)
            await handler.press_key("down")
            await asyncio.sleep(0.5)
            await handler.press_key("enter")
            await asyncio.sleep(2)
            
            await observer.observe_step("Selected unloading location", status="success")
            
        else:
            print("ERROR: Could not find unloading location field")
            await observer.observe_step("Failed to find unloading location field", status="failed")
            return
        
        # Step 7: Find and click "Поиск" button (green button)
        print("\n[7] Searching for 'Поиск' button...")
        screenshot = await screenshot_maker.take_screenshot(save_tag="step7_find_search")
        coords = await ocr.find_text_on_screen("Поиск", screenshot)
        
        if coords:
            x, y = coords
            print(f"Found 'Поиск' at ({x}, {y}), clicking...")
            await handler.click(x, y)
            await asyncio.sleep(3)
            
            await observer.observe_step("Clicked 'Поиск' button", screenshot=screenshot, status="success")
        else:
            print("WARNING: Could not find 'Поиск' button, trying 'Search'...")
            coords = await ocr.find_text_on_screen("Search", screenshot)
            if coords:
                x, y = coords
                await handler.click(x, y)
                await asyncio.sleep(3)
        
        print("\n" + "=" * 60)
        print("Automation completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        await observer.observe_step("Critical Error", details={"error": str(e)}, status="failed")
    finally:
        await observer.export("html", "ocr_automation_report.html")
        print(f"\nReport saved to: ocr_automation_report.html")

if __name__ == "__main__":
    asyncio.run(main())
