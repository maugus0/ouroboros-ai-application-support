"""Optional APScheduler wiring for deadline reminder scans (extracted for testability)."""

from typing import Protocol

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.jobs.deadline_reminder_job import run_deadline_reminder_scan


class _LoggerInfo(Protocol):
    def info(self, event: str, **kwargs: object) -> None: ...


def start_deadline_reminder_scheduler(
    *,
    enabled: bool,
    allow_db_failure: bool,
    interval_minutes: int,
    logger: _LoggerInfo,
) -> AsyncIOScheduler | None:
    """
    Start the deadline reminder job on an interval when enabled and DB is required.

    Returns the running scheduler instance, or None if scheduling was skipped.
    Caller must call ``shutdown(wait=True)`` on shutdown when non-None.
    """
    if not enabled or allow_db_failure:
        return None

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_deadline_reminder_scan,
        IntervalTrigger(minutes=max(1, interval_minutes)),
        id="deadline_reminder_scan",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "deadline_reminder_scheduler_started",
        interval_minutes=interval_minutes,
    )
    return scheduler
