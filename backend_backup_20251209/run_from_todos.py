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

async def execute_todo_step(step: dict, ocr: OCRHelper, handler: AsyncPyautoguiActionHandler, args):
    """
    Execute a single step from todos.json
    
    Step format:
    {
        "action": "click" | "type" | "press",
        "target": "text to find via OCR",
        "value": "text to type (for type action)",
        "description": "human readable description"
    }
    """
    action = step.get("action", "click")
    target = step.get("target")
    value = step.get("value", "")
    description = step.get("description", "Unnamed step")
    
    print(f"\n📋 {description}")
    
    # Take screenshot
    screenshot = pyautogui.screenshot()
    
    # Find target via OCR
    if target:
        print(f"   🔍 Looking for: '{target}'")
        coords = await ocr.find_text_on_screen(target, screenshot)
        
        if not coords:
            print(f"   ❌ Could not find '{target}' on screen")
            return False
        
        x, y = coords
        
        # Perform action
        if action == "click":
            print(f"   👆 Clicking at ({x}, {y})")
            await handler.move_to(x, y, duration=0.4)
            await handler.click(x, y)
            await asyncio.sleep(0.5)
            
        elif action == "type":
            print(f"   ⌨️  Clicking and typing: '{value}'")
            await handler.move_to(x, y, duration=0.4)
            await handler.click(x, y)
            await asyncio.sleep(0.3)
            
            # Replace placeholders
            if "{origin}" in value:
                value = value.replace("{origin}", args.origin)
            if "{destination}" in value:
                value = value.replace("{destination}", args.destination)
            
            await handler.hotkey("ctrl", "a")
            await handler.press_key("delete")
            await asyncio.sleep(0.2)
            await handler.type_text(value, interval=0.05)
            await asyncio.sleep(0.5)
            
        elif action == "press":
            key = value or "enter"
            print(f"   ⌨️  Pressing key: {key}")
            await handler.press_key(key)
            await asyncio.sleep(0.3)
    else:
        # Action without target (e.g., global hotkey)
        if action == "press":
            key = value or "enter"
            print(f"   ⌨️  Pressing key: {key}")
            await handler.press_key(key)
            await asyncio.sleep(0.3)
    
    return True

async def main():
    parser = argparse.ArgumentParser(description="Run automation from todos.json")
    parser.add_argument("--origin", "-o", default="Warszawa", help="Origin location")
    parser.add_argument("--destination", "-d", default="Berlin", help="Destination location")
    parser.add_argument("--todos", "-t", default="todos.json", help="Path to todos.json file")
    
    args = parser.parse_args()

    print("=" * 60)
    print(f"TODO-BASED AUTOMATION")
    print(f"Origin: {args.origin}")
    print(f"Destination: {args.destination}")
    print(f"Todos file: {args.todos}")
    print("=" * 60)

    # Load todos
    todos_path = Path(args.todos)
    if not todos_path.exists():
        # Try looking in root
        todos_path = Path(os.getcwd()) / args.todos
        
    if not todos_path.exists():
        print(f"❌ Todos file not found: {args.todos}")
        return

    with open(todos_path, "r", encoding="utf-8") as f:
        todos = json.load(f)

    if not isinstance(todos, list):
        print("❌ Todos file must contain a JSON array of steps")
        return

    print(f"✓ Loaded {len(todos)} steps from {args.todos}")

    observer = AsyncAgentObserver()
    observer.set_agent_name("Todo-Bot")
    
    handler = AsyncPyautoguiActionHandler()
    screenshot_maker = AsyncScreenshotMaker(save_history=True)
    ocr = OCRHelper()
    
    try:
        print("\n⚠️  PLEASE BRING YOUR BROWSER WINDOW TO THE FRONT! ⚠️")
        print("Starting in 5 seconds...")
        await asyncio.sleep(5)
        
        # Execute each step
        for i, step in enumerate(todos, 1):
            print(f"\n{'='*60}")
            print(f"STEP {i}/{len(todos)}")
            print(f"{'='*60}")
            
            success = await execute_todo_step(step, ocr, handler, args)
            
            if not success:
                print(f"\n⚠️  Step {i} failed. Continue anyway? (Y/n)")
                # For now, continue automatically
                # You can add input() here if you want manual confirmation
                pass
            
            # Wait between steps
            await asyncio.sleep(1.0)
        
        print("\n" + "=" * 60)
        print("✅ All steps completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
