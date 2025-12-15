import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.tasks import launch_browser_task

async def main():
    print("Testing launch_browser_task...")
    await launch_browser_task()
    print("Task completed. Browser should be open.")
    # Keep script running so browser stays open
    await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
