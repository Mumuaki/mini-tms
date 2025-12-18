import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pyautogui

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.automation import AsyncAgentObserver, AsyncPyautoguiActionHandler, AsyncScreenshotMaker
from app.services.automation.ocr_helper import OCRHelper

async def main():
    parser = argparse.ArgumentParser(description="Run Smart Visual Automation")
    parser.add_argument("--origin", "-o", default="Warszawa", help="Origin location")
    parser.add_argument("--destination", "-d", default="Berlin", help="Destination location")
    
    args = parser.parse_args()

    print("=" * 60)
    print(f"SMART OCR AUTOMATION")
    print(f"Task: {args.origin} -> {args.destination}")
    print("=" * 60)

    observer = AsyncAgentObserver()
    handler = AsyncPyautoguiActionHandler()
    screenshot_maker = AsyncScreenshotMaker(save_history=True)
    ocr = OCRHelper()
    
    async def smart_click_between(screenshot, label_text, below_text_hint, desc):
        """Finds a click target between two text elements."""
        print(f"\n   🎯 Targeting '{desc}'...")
        
        # 1. Find Top Label (Try exact, then fuzzy)
        label = await ocr.find_text_on_screen(label_text, screenshot)
        
        if not label:
            # Fuzzy fallback
            print(f"      ℹ️ Exact match for '{label_text}' not found. Trying fuzzy...")
            all_text = await ocr.find_all_text_on_screen(screenshot)
            import difflib
            texts = [t['text'] for t in all_text]
            matches = difflib.get_close_matches(label_text, texts, n=1, cutoff=0.6)
            
            if matches:
                best_match = matches[0]
                for item in all_text:
                    if item['text'] == best_match:
                        label = (item['x'], item['y'])
                        print(f"      ✓ Found fuzzy match: '{best_match}'")
                        break
        
        if not label:
            print(f"      ❌ Label '{label_text}' not found.")
            # Dump first 20 texts for debug
            print("      DEBUG: Top 20 texts found on screen:")
            all_text = await ocr.find_all_text_on_screen(screenshot)
            for i, t in enumerate(all_text[:20]):
                print(f"         [{i}] {t['text']}")
            return False
            
        # 2. Find Bottom Reference (optional, fallback to offset)
        # We search for text that is BELOW the label (y > label_y) and close in X
        all_text = await ocr.find_all_text_on_screen(screenshot)
        below_candidates = []
        
        for item in all_text:
            if item['y'] > label[1] + 20 and item['y'] < label[1] + 150: # Look within 150px below
                if abs(item['x'] - label[0]) < 100: # Roughly same column
                    below_candidates.append(item)
        
        # Sort by Y to find the nearest one
        below_candidates.sort(key=lambda k: k['y'])
        
        target_x = label[0] + 20 # Slight indent right
        target_y = 0
        
        if below_candidates:
            nearest = below_candidates[0]
            print(f"      ✓ Found reference below: '{nearest['text']}' at Y={nearest['y']}")
            # Midpoint
            target_y = (label[1] + nearest['y']) // 2
        else:
            print(f"      ⚠️ No reference text found below '{label_text}'. Using default offset.")
            target_y = label[1] + 45 # Default fallback
            
        print(f"      ✓ Calculated Target: ({target_x}, {target_y})")
        
        # Execute Click
        await handler.move_to(target_x, target_y, duration=0.4)
        await handler.click(target_x, target_y)
        return True

    try:
        print("\n⚠️  PLEASE BRING YOUR BROWSER WINDOW TO THE FRONT! ⚠️")
        print("Starting in 5 seconds...")
        await asyncio.sleep(5)
        
        # --- STEP -1: REFRESH PAGE ---
        print("\n[-1] 🔄 Refreshing 'Freight search' page...")
        # Look for "Freight search" text in left menu
        screenshot = await screenshot_maker.take_screenshot(save_tag="step_pre_refresh")
        freight_search = await ocr.find_text_on_screen("Freight search", screenshot)
        
        if not freight_search:
            freight_search = await ocr.find_text_on_screen("FREIGHT SEARCH", screenshot)
        
        if freight_search:
            print(f"   ✓ Found 'Freight search' menu item at {freight_search}")
            await handler.click(freight_search[0], freight_search[1])
            print("   ⏳ Waiting for page to load...")
            await asyncio.sleep(3.0)
        else:
            print("   ⚠️ Could not find 'Freight search' menu item. Assuming already on the page.")
        
        # --- STEP 0a: VERIFY URL ---
        print("\n[0a] 🔍 Verifying URL...")
        screenshot = await screenshot_maker.take_screenshot(save_tag="step0a_url_check")
        
        # Try to find the URL in address bar
        url_found = await ocr.find_text_on_screen("platform.trans.eu/exchange/offers", screenshot)
        
        if url_found:
            print("   ✓ Confirmed: On correct page (URL contains 'platform.trans.eu/exchange/offers')")
        else:
            print("   ⚠️ WARNING: Could not verify URL via OCR. Proceeding anyway...")
        
        # --- STEP 0: EXPAND FILTERS ---
        print("\n[0] 🔍 Checking Filters...")
        screenshot = await screenshot_maker.take_screenshot(save_tag="step0_init")
        
        # Try to find expand button (English: "EXPAND FILTERS" or "SHOW MORE")
        expand_btn = await ocr.find_text_on_screen("EXPAND FILTERS", screenshot)
        if not expand_btn:
             expand_btn = await ocr.find_text_on_screen("SHOW MORE", screenshot)
        if not expand_btn:
             expand_btn = await ocr.find_text_on_screen("EXPAND", screenshot)
        
        # Try to find collapse button (maybe already open?)
        collapse_btn = await ocr.find_text_on_screen("COLLAPSE FILTERS", screenshot)
        if not collapse_btn:
             collapse_btn = await ocr.find_text_on_screen("SHOW LESS", screenshot)
        if not collapse_btn:
             collapse_btn = await ocr.find_text_on_screen("COLLAPSE", screenshot)

        # Try to find the field label directly (English: "Loading")
        loading_label = await ocr.find_text_on_screen("Loading", screenshot)

        if loading_label:
            print("   ✓ Filters appear to be already expanded ('Loading' is visible).")
        elif collapse_btn:
            print("   ✓ Filters are already expanded (Found 'COLLAPSE').")
        elif expand_btn:
            print(f"   ✓ Found 'EXPAND FILTERS'. Clicking...")
            await handler.click(expand_btn[0], expand_btn[1])
            print("   ⏳ Waiting 3 seconds for animation...")
            await asyncio.sleep(3.0)
            # Update screenshot
            screenshot = await screenshot_maker.take_screenshot(save_tag="step0_expanded")
        else:
            print("   ❌ CRITICAL: Could not find 'EXPAND', 'COLLAPSE' or 'Loading'.")
            print("   DEBUG: Dumping all text found on screen:")
            all_text = await ocr.find_all_text_on_screen(screenshot)
            for i, t in enumerate(all_text):
                print(f"      [{i}] '{t['text']}' at ({t['x']}, {t['y']})")
            return # STOP HERE

        # --- STEP 1: LOADING ---
        print("\n[1] 🌍 Handling Loading Location...")
        
        # Strategy: Find the field by looking for country code pattern (e.g., "AT, 2822")
        # This is more reliable than guessing offsets
        all_text = await ocr.find_all_text_on_screen(screenshot)
        import re
        
        loading_field_text = None
        for item in all_text:
            # Match pattern: "XX, " where XX are 2 uppercase letters
            if re.match(r'^[A-Z]{2},\s', item['text']):
                # Check if this is near "Loading" label (within 100px below)
                loading_label = await ocr.find_text_on_screen("Loading", screenshot)
                if loading_label and item['y'] > loading_label[1] and item['y'] < loading_label[1] + 100:
                    loading_field_text = item
                    break
        
        if loading_field_text:
            print(f"   ✓ Found loading field with current value: '{loading_field_text['text']}'")
            # Click on it
            await handler.move_to(loading_field_text['x'], loading_field_text['y'], duration=0.4)
            await handler.click(loading_field_text['x'], loading_field_text['y'])
            
            # Wait for modal to appear
            print("   ⏳ Waiting for modal window...")
            await asyncio.sleep(1.5)
            
            # Clear and type
            await handler.hotkey("ctrl", "a")
            await handler.press_key("delete")
            await asyncio.sleep(0.3)
            await handler.type_text(args.origin, interval=0.05)
            print(f"   ✓ Typed: {args.origin}")
            await asyncio.sleep(1.5) # Wait for suggestions
            await handler.press_key("down")
            await asyncio.sleep(0.3)
            await handler.press_key("enter")
            await asyncio.sleep(1.5) # Wait for modal to close
            
            # REFRESH SCREENSHOT after modal closes
            screenshot = await screenshot_maker.take_screenshot(save_tag="step1_after_loading")
        else:
            # Fallback to old method
            if await smart_click_between(screenshot, "Loading", None, "Loading Field"):
                await asyncio.sleep(1.5)
                await handler.hotkey("ctrl", "a")
                await handler.press_key("delete")
                await handler.type_text(args.origin, interval=0.05)
                await asyncio.sleep(1.5)
                await handler.press_key("down")
                await handler.press_key("enter")
                await asyncio.sleep(1.5)
                # REFRESH SCREENSHOT
                screenshot = await screenshot_maker.take_screenshot(save_tag="step1_after_loading_fallback")
            else:
                return

        # --- STEP 2: UNLOADING ---
        print("\n[2] 🏁 Handling Unloading Location...")
        
        # REFRESH all_text with new screenshot
        all_text = await ocr.find_all_text_on_screen(screenshot)
        
        # Find unloading field by country code pattern
        unloading_field_text = None
        for item in all_text:
            if re.match(r'^[A-Z]{2},\s', item['text']):
                # Check if this is near "Unloading" label
                unloading_label = await ocr.find_text_on_screen("Unloading", screenshot)
                if unloading_label and item['y'] > unloading_label[1] and item['y'] < unloading_label[1] + 100:
                    # Make sure it's not the same as loading field
                    if loading_field_text and item['text'] != loading_field_text['text']:
                        unloading_field_text = item
                        break
        
        if unloading_field_text:
            print(f"   ✓ Found unloading field with current value: '{unloading_field_text['text']}'")
            await handler.move_to(unloading_field_text['x'], unloading_field_text['y'], duration=0.4)
            await handler.click(unloading_field_text['x'], unloading_field_text['y'])
            print("   ⏳ Waiting for modal window...")
            await asyncio.sleep(1.5)
            await handler.hotkey("ctrl", "a")
            await handler.press_key("delete")
            await asyncio.sleep(0.3)
            await handler.type_text(args.destination, interval=0.05)
            print(f"   ✓ Typed: {args.destination}")
            await asyncio.sleep(1.5)
            await handler.press_key("down")
            await asyncio.sleep(0.3)
            await handler.press_key("enter")
            await asyncio.sleep(1.5)
            
            # REFRESH SCREENSHOT
            screenshot = await screenshot_maker.take_screenshot(save_tag="step2_after_unloading")
        else:
            # Fallback
            if await smart_click_between(screenshot, "Unloading", None, "Unloading Field"):
                await asyncio.sleep(1.5)
                await handler.hotkey("ctrl", "a")
                await handler.press_key("delete")
                await handler.type_text(args.destination, interval=0.05)
                await asyncio.sleep(1.5)
                await handler.press_key("down")
                await handler.press_key("enter")
                await asyncio.sleep(1.5)
                # REFRESH SCREENSHOT
                screenshot = await screenshot_maker.take_screenshot(save_tag="step2_after_unloading_fallback")

        # --- STEP 3: DATES ---
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        if await smart_click_between(screenshot, "Loading date", None, "Loading Date"):
            await asyncio.sleep(0.5)
            await handler.type_text(tomorrow, interval=0.05)
            await handler.press_key("enter")

        # --- STEP 4: SEARCH ---
        print("\n[4] 🔍 Searching...")
        # Find green button "Search" on the right
        all_search = [i for i in await ocr.find_all_text_on_screen(screenshot) if "Search" in i['text']]
        # Filter: Right side (x > 500)
        btn = next((i for i in all_search if i['x'] > 500), None)
        
        if btn:
            print(f"   ✓ Found Search button at ({btn['x']}, {btn['y']})")
            await handler.click(btn['x'], btn['y'])
        else:
            print("   ❌ Search button not found!")

        print("\n✅ Done!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
