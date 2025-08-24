from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.config import config
from app.tasks import main_task, daily_summary, six_hourly_summary

logger = logging.getLogger(__name__)

def run_scheduler():
    """Initializes and runs the scheduler for background tasks."""
    scheduler = BlockingScheduler(timezone=config["TZ"])

    scheduler.add_job(
        main_task,
        "interval",
        minutes=config["interval_minutes"],
        id="main_task",
        replace_existing=True,
    )

    scheduler.add_job(
        six_hourly_summary,
        "interval",
        hours=6,
        id="six_hourly_summary",
        replace_existing=True,
    )

    scheduler.add_job(
        daily_summary,
        CronTrigger(hour=8, minute=30, timezone=config["TZ"]),
        id="daily_summary",
        replace_existing=True,
    )

    logger.info("Scheduler started. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass