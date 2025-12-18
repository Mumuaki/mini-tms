<<<<<<< HEAD
#!/usr/bin/env python3
"""
Mini-TMS Backend Entry Point
"""

import uvicorn
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Development mode
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )

=======
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
>>>>>>> 97953c3 (Initial commit from Specify template)
