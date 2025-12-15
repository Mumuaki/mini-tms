import asyncio
import pyautogui
from typing import Optional

class AsyncPyautoguiActionHandler:
    """
    Asynchronous handler for mouse and keyboard actions using PyAutoGUI.
    Executes actions in a separate thread to avoid blocking the main event loop.
    """
    
    def __init__(self):
        # Fail-safe: moving mouse to upper-left corner will abort
        pyautogui.FAILSAFE = True
        # Set a small pause between actions
        pyautogui.PAUSE = 0.5

    async def click(self, x: int, y: int, button: str = 'left', clicks: int = 1):
        """Click at specific coordinates."""
        await self._run(pyautogui.click, x=x, y=y, button=button, clicks=clicks)

    async def type_text(self, text: str, interval: float = 0.05):
        """Type text with a delay between keystrokes."""
        await self._run(pyautogui.write, message=text, interval=interval)

    async def press_key(self, key: str):
        """Press a specific key (e.g., 'enter', 'tab', 'esc')."""
        await self._run(pyautogui.press, keys=key)

    async def scroll(self, clicks: int):
        """Scroll the mouse wheel (positive = up, negative = down)."""
        await self._run(pyautogui.scroll, clicks=clicks)

    async def move_to(self, x: int, y: int, duration: float = 0.5):
        """Move mouse to coordinates."""
        await self._run(pyautogui.moveTo, x=x, y=y, duration=duration)

    async def drag_to(self, x: int, y: int, duration: float = 0.5):
        """Drag mouse to coordinates."""
        await self._run(pyautogui.dragTo, x=x, y=y, duration=duration)
        
    async def hotkey(self, *keys):
        """Press a combination of keys (e.g., 'ctrl', 'c')."""
        await self._run(pyautogui.hotkey, *keys)

    async def _run(self, func, *args, **kwargs):
        """Helper to run synchronous pyautogui functions in an executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
