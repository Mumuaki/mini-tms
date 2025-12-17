import sys
import asyncio
import uvicorn

# Fix for Windows asyncio loop with subprocesses (required for Playwright)
# Moved inside main block to avoid issues with reload


if __name__ == "__main__":
    print("Setting WindowsProactorEventLoopPolicy...")
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Import app AFTER setting the policy
    from app.main import app
    
    print("Starting server with reload=False to support Playwright...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
