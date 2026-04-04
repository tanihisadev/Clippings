from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.config import Config
from src.scheduler.runner import DigestRunner
import asyncio


class DigestScheduler:
    """Schedule daily digest runs."""

    def __init__(self, config: Config):
        self.config = config
        self.scheduler = BlockingScheduler()

    def setup(self) -> None:
        """Set up the daily digest schedule."""
        hour, minute = self.config.schedule.time.split(":")
        self.scheduler.add_job(
            self._run_digest,
            CronTrigger(hour=int(hour), minute=int(minute), timezone=self.config.schedule.timezone),
            id="daily_digest",
            name="Daily Clippings",
            replace_existing=True,
        )
        print(f"Scheduled daily digest at {self.config.schedule.time} {self.config.schedule.timezone}")

    def start(self) -> None:
        """Start the scheduler."""
        self.setup()
        print("Starting scheduler...")
        self.scheduler.start()

    def get_next_run(self) -> str:
        """Get the next scheduled run time."""
        hour, minute = self.config.schedule.time.split(":")
        return f"Daily at {hour}:{minute} {self.config.schedule.timezone}"

    def _run_digest(self) -> None:
        """Run the digest pipeline synchronously."""
        runner = DigestRunner(self.config)
        asyncio.run(runner.run())
