import sys
import asyncio
import uvicorn

# Fix for Windows asyncio loop with subprocesses (required for Playwright)
# Moved inside main block to avoid issues with reload


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("Starting Mini-TMS Backend with WindowsProactorEventLoopPolicy...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
