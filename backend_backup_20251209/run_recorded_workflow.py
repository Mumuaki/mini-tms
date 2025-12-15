import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import pyautogui

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.automation import AsyncAgentObserver, AsyncPyautoguiActionHandler, AsyncScreenshotMaker
from app.services.automation.ocr_helper import OCRHelper

async def main():
    parser = argparse.ArgumentParser(description="Run Recorded Workflow")
    parser.add_argument("--origin", "-o", default="Warszawa", help="Origin location")
    parser.add_argument("--destination", "-d", default="Berlin", help="Destination location")
    parser.add_argument("--workflow", "-w", default="recorded_workflow.json", help="Path to workflow file")
    
    args = parser.parse_args()

    print("=" * 60)
    print(f"PLAYING RECORDED WORKFLOW")
    print(f"Task: {args.origin} -> {args.destination}")
    print("=" * 60)

    # Load workflow
    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        # Try looking in root if not found
        workflow_path = Path(os.getcwd()) / args.workflow
        
    if not workflow_path.exists():
        print(f"❌ Workflow file not found: {args.workflow}")
        return

    with open(workflow_path, "r", encoding="utf-8") as f:
        steps = json.load(f)

    # Filter steps (remove the one marked for deletion)
    steps = [s for s in steps if "удали этот пункт" not in s.get("value", "") and "удали этот пункт" not in s.get("description", "")]

    observer = AsyncAgentObserver()
    observer.set_agent_name("Replay-Bot")
    
    handler = AsyncPyautoguiActionHandler()
    screenshot_maker = AsyncScreenshotMaker(save_history=True)
    ocr = OCRHelper()
    
    try:
        print("\n⚠️  PLEASE BRING YOUR BROWSER WINDOW TO THE FRONT! ⚠️")
        print("Starting in 5 seconds...")
        await asyncio.sleep(5)
        
        for i, step in enumerate(steps):
            print(f"\n--- STEP {i+1}: {step.get('description', 'Unnamed')} ---")
            
            # 1. Find Anchor
            anchor_text = step.get("anchor_text")
            target_x, target_y = step["x"], step["y"] # Default to recorded abs coords
            
            if anchor_text:
                print(f"   🔍 Looking for anchor: '{anchor_text}'...")
                screenshot = await screenshot_maker.take_screenshot(save_tag=f"step{i}_search")
                
                # Try to find exact or fuzzy match
                found_anchor = await ocr.find_text_on_screen(anchor_text, screenshot)
                
                # If not found, try finding something very similar from all text
                if not found_anchor:
                    all_text = await ocr.find_all_text_on_screen(screenshot)
                    import difflib
                    # Find closest string match
                    texts = [t['text'] for t in all_text]
                    matches = difflib.get_close_matches(anchor_text, texts, n=1, cutoff=0.6)
                    
                    if matches:
                        best_match_text = matches[0]
                        for item in all_text:
                            if item['text'] == best_match_text:
                                found_anchor = (item['x'], item['y'])
                                print(f"   ✓ Found fuzzy match: '{best_match_text}'")
                                break
                
                if found_anchor:
                    # Calculate new target based on offset
                    target_x = found_anchor[0] + step["offset_x"]
                    target_y = found_anchor[1] + step["offset_y"]
                    print(f"   ✅ Anchor found at {found_anchor}. Target adjusted to ({target_x}, {target_y})")
                else:
                    print(f"   ⚠️ Anchor '{anchor_text}' NOT found. Using absolute recorded coordinates.")
            
            # 2. Move and Perform Action
            print(f"   > Moving to ({target_x}, {target_y})...")
            await handler.move_to(target_x, target_y, duration=0.3) # Faster move
            
            action = step.get("action", "click")
            
            if action == "click":
                await handler.click(target_x, target_y)
                print("   > Clicked")
                await asyncio.sleep(0.3) # Shorter wait
                
            elif action == "type":
                # Click first to focus
                await handler.click(target_x, target_y)
                await asyncio.sleep(0.2)
                
                # Determine value to type
                value = step.get("value", "")
                if "{type new addres" in value:
                    value = args.origin
                elif "{text here required" in value:
                    value = args.destination
                
                print(f"   > Typing: '{value}'")
                await handler.type_text(value, interval=0.01) # Faster typing
                await asyncio.sleep(0.5)
                
            elif action == "press":
                key = step.get("value", "enter")
                print(f"   > Pressing key: {key}")
                await handler.press_key(key)
                await asyncio.sleep(0.2)

        print("\n" + "=" * 60)
        print("Workflow Replay Completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
