import asyncio
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.automation import AsyncAgentObserver
from app.services.trans_eu import TransEuScraper
from app.services.automation.tools import AutomationTools

async def main():
    parser = argparse.ArgumentParser(description="Run Trans.eu Scraper with Playwright")
    
    parser.add_argument("--origin", "-o", default="Warszawa", help="Origin location")
    parser.add_argument("--destination", "-d", default="Berlin", help="Destination location")
    parser.add_argument("--output", default="scraper_report.html", help="Output report file")
    
    args = parser.parse_args()

    print("=" * 60)
    print(f"Starting Trans.eu Playwright Scraper")
    print(f"Task: Find freights {args.origin} -> {args.destination}")
    print("=" * 60)

    # Initialize Observer
    observer = AsyncAgentObserver()
    observer.set_agent_name("TransEuPlaywrightBot")
    
    # Initialize Tools
    tools = AutomationTools()
    
    # Initialize Scraper
    scraper = TransEuScraper()
    
    try:
        await observer.observe_step("Starting browser", status="info")
        
        # Start browser
        await scraper.start_browser(headless=False)
        
        await observer.observe_step("Browser started", status="success")
        
        # Check if logged in
        if not scraper.is_logged_in:
            await observer.observe_step("Attempting login", status="info")
            await scraper.login()
            await observer.observe_step("Login completed", status="success")
        
        # Navigate to offers page
        await observer.observe_step("Navigating to offers page", status="info")
        await scraper.page.goto(scraper.freights_url, wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(2)
        
        # Apply filters using the existing scraper logic
        filters = {
            "origin": args.origin,
            "destination": args.destination
        }
        
        await observer.observe_step(
            "Applying filters", 
            details=filters,
            status="info"
        )
        
        await scraper._apply_filters(filters)
        
        await observer.observe_step("Filters applied", status="success")
        
        # Parse results
        await observer.observe_step("Parsing freight list", status="info")
        freights = await scraper._parse_freight_list()
        
        await observer.observe_step(
            f"Found {len(freights)} freights",
            details={"count": len(freights)},
            status="success"
        )
        
        # Analyze first 3 freights with tools
        for i, freight in enumerate(freights[:3]):
            print(f"\n--- Analyzing Freight {i+1} ---")
            print(f"Route: {freight.get('loading_place')} -> {freight.get('unloading_place')}")
            print(f"Price: {freight.get('price_original')}")
            
            # Calculate distance
            if freight.get('loading_place') and freight.get('unloading_place'):
                distance_result = tools.calculate_distance(
                    freight['loading_place'],
                    freight['unloading_place']
                )
                print(f"Distance: {distance_result}")
                
                # Calculate profit
                try:
                    price = float(freight.get('price_original', '0').replace('EUR', '').replace(',', '.').strip())
                    distance_km = float(distance_result.replace('km', '').strip())
                    
                    profit_result = tools.calculate_profit(price, distance_km)
                    print(f"Profit Analysis: {profit_result}")
                    
                    await observer.observe_step(
                        f"Analyzed Freight {i+1}",
                        details={
                            "route": f"{freight['loading_place']} -> {freight['unloading_place']}",
                            "distance": distance_result,
                            "profit": profit_result
                        },
                        status="success"
                    )
                except Exception as e:
                    print(f"Error calculating profit: {e}")
        
        print("\nExecution finished.")
        
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nCritical Error: {e}")
        import traceback
        traceback.print_exc()
        await observer.observe_step("Critical Error", details={"error": str(e)}, status="failed")
    finally:
        # Export Report
        await observer.export("html", args.output)
        print(f"Report saved to: {os.path.abspath(args.output)}")
        
        # Keep browser open for inspection
        print("\nBrowser will remain open. Press Ctrl+C to close.")
        try:
            await asyncio.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    asyncio.run(main())
