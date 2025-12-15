import asyncio
import base64
import io
import os
from datetime import datetime
from typing import Optional, Union, Tuple
import pyautogui
from playwright.async_api import Page

class AsyncScreenshotMaker:
    """
    Asynchronous screenshot provider for automation agents.
    Can capture both full screen (via PyAutoGUI) and browser viewport (via Playwright).
    
    This class is designed to:
    1. Provide visual context for AI agents.
    2. Enable visual debugging by capturing state at each step.
    3. Support both OS-level and Browser-level automation.
    """
    
    def __init__(self, save_history: bool = False, history_dir: str = "screenshots_history"):
        """
        Initialize the screenshot maker.
        
        Args:
            save_history: If True, saves screenshots to disk for debugging/history.
            history_dir: Directory to save history screenshots.
        """
        self.save_history = save_history
        self.history_dir = history_dir
        
        if self.save_history and not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir, exist_ok=True)

    async def take_screenshot(self, page: Optional[Page] = None, save_tag: str = None) -> str:
        """
        Takes a screenshot and returns it as a base64 encoded string.
        
        Args:
            page: Optional Playwright Page object. If provided, captures the browser viewport.
                  If None, captures the entire primary screen using PyAutoGUI.
            save_tag: Optional tag for the filename if saving history (e.g. "step_1_login").
                  
        Returns:
            str: Base64 encoded image string (JPEG format).
        """
        if page:
            b64_img = await self._take_browser_screenshot(page)
            source = "browser"
        else:
            b64_img = await self._take_screen_screenshot()
            source = "screen"
            
        if self.save_history:
            await self._save_to_disk(b64_img, source, save_tag)
            
        return b64_img

    async def _take_browser_screenshot(self, page: Page) -> str:
        """Captures browser viewport using Playwright."""
        try:
            # Take screenshot as JPEG to reduce size for AI models
            screenshot_bytes = await page.screenshot(type='jpeg', quality=80)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error taking browser screenshot: {e}")
            # Fallback to screen screenshot if browser fails
            return await self._take_screen_screenshot()

    async def _take_screen_screenshot(self) -> str:
        """Captures full screen using PyAutoGUI (run in executor to be non-blocking)."""
        loop = asyncio.get_running_loop()
        
        def _capture():
            try:
                # pyautogui.screenshot() returns a PIL Image
                img = pyautogui.screenshot()
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=80)
                return buffer.getvalue()
            except Exception as e:
                print(f"Error taking screen screenshot: {e}")
                return b""

        screenshot_bytes = await loop.run_in_executor(None, _capture)
        return base64.b64encode(screenshot_bytes).decode('utf-8')

    async def _save_to_disk(self, b64_img: str, source: str, tag: str = None):
        """Saves the base64 image to disk asynchronously."""
        if not b64_img:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        tag_str = f"_{tag}" if tag else ""
        filename = f"{timestamp}_{source}{tag_str}.jpg"
        filepath = os.path.join(self.history_dir, filename)
        
        loop = asyncio.get_running_loop()
        
        def _write():
            try:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(b64_img))
            except Exception as e:
                print(f"Failed to save screenshot history: {e}")
                
        await loop.run_in_executor(None, _write)
