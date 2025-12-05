"""
Background tasks for Mini-TMS
Handles scheduled scraping, GPS updates, etc.
"""

from datetime import datetime
from typing import Optional
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None


async def init_scheduler():
    """Initialize background task scheduler"""
    global scheduler
    scheduler = AsyncIOScheduler()
    
    # GPS Update Task (every 30 minutes)
    scheduler.add_job(
        run_gps_update_task,
        trigger=IntervalTrigger(minutes=30),
        id='gps_update',
        name='Update GPS coordinates',
        replace_existing=True
    )
    
    # Scraper Task (every 60 minutes)
    scheduler.add_job(
        run_scraper_task,
        trigger=IntervalTrigger(minutes=60),
        id='scraper',
        name='Scrape Trans.eu freights',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Background scheduler started")


async def shutdown_scheduler():
    """Shutdown background task scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        logger.info("✅ Background scheduler stopped")


async def run_gps_update_task():
    """
    Scheduled task to update GPS for all trucks
    Called every 30 minutes
    """
    try:
        logger.info("🔄 Running scheduled GPS update task...")
        # TODO: Implement GPS update logic
        # from app.services.gps_service import GPSService
        # gps_service = GPSService()
        # await gps_service.update_all_trucks()
        logger.info("✅ GPS update task completed")
    except Exception as e:
        logger.error(f"❌ GPS update task failed: {str(e)}")


async def run_scraper_task():
    """
    Scheduled task to scrape Trans.eu
    Called every 60 minutes
    """
    try:
        logger.info("🕷️ Running scheduled scraper task...")
        # TODO: Implement scraper logic
        # from app.services.transeu import TransEuScraper
        # scraper = TransEuScraper()
        # await scraper.scrape_freights()
        logger.info("✅ Scraper task completed")
    except Exception as e:
        logger.error(f"❌ Scraper task failed: {str(e)}")


def get_scheduler_status():
    """Get status of background scheduler"""
    if scheduler is None:
        return {"status": "not_initialized"}
    
    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": len(scheduler.get_jobs()),
        "jobs_detail": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }
