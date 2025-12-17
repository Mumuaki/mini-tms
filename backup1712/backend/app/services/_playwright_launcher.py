import asyncio
import sys
import os
import subprocess
import time

# Ensure ProactorEventLoopPolicy is used for subprocesses on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def launch_playwright_browser_standalone(cdp_port: int, profile_dir: str):
    """
    Launches a Playwright Chromium browser in a separate process
    with a remote debugging port and user data directory.
    """
    print(f"[{os.getpid()}] Standalone launcher: Attempting to launch browser on port {cdp_port}")

    # Find chrome executable (similar logic as in ScraperManager)
    def _find_chrome_executable() -> str:
        env_path = os.getenv("CHROME_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "/usr/bin/google-chrome",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        raise FileNotFoundError("Браузер не найден. Установите переменную CHROME_PATH.")

    exe_path = _find_chrome_executable()
    os.makedirs(profile_dir, exist_ok=True)

    args = [
        exe_path,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        "--disable-infobars",
        "--disable-gpu",
    ]

    print(f"[{os.getpid()}] Standalone launcher: Executing command: {' '.join(args)}")
    
    # Launch Chrome subprocess directly, let it print to console
    # The parent process (ScraperManager) will handle the connection check
    process = subprocess.Popen(
        args,
        stdout=sys.stdout, # IMPORTANT: Direct output to console for debugging
        stderr=sys.stderr, # IMPORTANT: Direct output to console for debugging
        shell=False,
    )

    print(f"[{os.getpid()}] Standalone launcher: Chrome process started with PID {process.pid}")
    
    # We exit after launching, letting the parent process handle connection and further checks.
    # We do NOT wait for the port to become active here, that's ScraperManager's job.

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python _playwright_launcher.py <CDP_PORT> <PROFILE_DIR>")
        sys.exit(1)
    
    cdp_port = int(sys.argv[1])
    profile_dir = sys.argv[2]
    
    # Run the async launcher with a dummy event loop for Popen, just to be sure
    # Popen itself is not async, but the async context might be needed for other things
    # within the launcher if it were more complex. Here, it's just for consistency.
    try:
        asyncio.run(launch_playwright_browser_standalone(cdp_port, profile_dir))
    except FileNotFoundError as e:
        print(f"[{os.getpid()}] Standalone launcher: ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[{os.getpid()}] Standalone launcher: General ERROR: {e}")
        sys.exit(1)