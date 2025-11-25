from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.utils.logging import logger
from app.database import db
import httpx
from datetime import datetime
import pytz

def trigger_daily_simulation():
    """
    Trigger the daily simulation via API.
    This runs in a separate thread managed by APScheduler.
    """
    logger.info("Scheduler triggering daily simulation...")
    
    # We need to run the async HTTP call in a sync context
    try:
        # Use a new event loop for this thread if needed, or run_in_executor
        # Since this is a sync method called by APScheduler, we can use httpx.Client (sync)
        # or asyncio.run() with httpx.AsyncClient.
        # Using sync Client for simplicity in this thread.
        
        headers = {"x-admin-key": settings.ADMIN_API_KEY}
        url = f"{settings.API_BASE_URL}/admin/simulate/day"
        
        with httpx.Client(timeout=300.0) as client: # 5 min timeout for long simulation
            response = client.post(url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Scheduled simulation completed successfully: {response.json()}")
            else:
                logger.error(f"Scheduled simulation failed with status {response.status_code}: {response.text}")
                
    except Exception as e:
        logger.error(f"Error in scheduled simulation job: {str(e)}")

class SchedulerService:
    def __init__(self):
        self.scheduler = None
        self.job_id = "daily_simulation"

    def start(self):
        """Initialize and start the scheduler."""
        if not settings.ENABLE_SCHEDULER:
            logger.info("Scheduler is disabled via configuration.")
            return

        try:
            # Configure MongoDB job store
            jobstores = {
                'default': MongoDBJobStore(
                    database=settings.DB_NAME,
                    collection='scheduled_jobs',
                    client=db.client
                )
            }

            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                timezone=pytz.timezone(settings.TIMEZONE)
            )

            # Add or update the daily simulation job
            # We use replace_existing=True to ensure config changes (like time) are applied
            hour, minute = settings.SCHEDULE_TIME.split(":")
            
            self.scheduler.add_job(
                trigger_daily_simulation,
                trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=pytz.timezone(settings.TIMEZONE)),
                id=self.job_id,
                replace_existing=True,
                name="Daily Simulation Pipeline"
            )

            self.scheduler.start()
            logger.info(f"Scheduler started. Daily simulation scheduled for {settings.SCHEDULE_TIME} ({settings.TIMEZONE})")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            # Don't raise, just log. We don't want to crash the app if scheduler fails.

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down.")

scheduler_service = SchedulerService()
