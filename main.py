import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import SCHEDULE_HOURS
from db import init_db
from pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("internship-bot")

async def main():
    await init_db()
    logger.info("Database initialized")

    # Run once immediately on startup
    logger.info("Running initial scan...")
    await run_pipeline()

    # Schedule recurring runs
    scheduler = AsyncIOScheduler()
    for hour in SCHEDULE_HOURS:
        scheduler.add_job(
            run_pipeline,
            trigger=CronTrigger(hour=hour, minute=0),
            id=f"scan_{hour}",
            name=f"Internship scan at {hour}:00 UTC",
        )
    scheduler.start()
    logger.info(f"Scheduler started. Runs at hours: {SCHEDULE_HOURS} UTC")

    # Keep the process alive
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Shut down.")

if __name__ == "__main__":
    asyncio.run(main())
