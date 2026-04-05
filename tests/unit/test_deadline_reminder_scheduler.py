"""Unit tests for deadline reminder APScheduler wiring."""

from unittest.mock import MagicMock, patch

from app.jobs.deadline_reminder_job import run_deadline_reminder_scan
from app.jobs.deadline_reminder_scheduler import start_deadline_reminder_scheduler


def test_scheduler_skipped_when_disabled():
    log = MagicMock()
    scheduler = start_deadline_reminder_scheduler(
        enabled=False,
        allow_db_failure=False,
        interval_minutes=60,
        logger=log,
    )
    assert scheduler is None
    log.info.assert_not_called()


def test_scheduler_skipped_when_db_failure_allowed():
    log = MagicMock()
    scheduler = start_deadline_reminder_scheduler(
        enabled=True,
        allow_db_failure=True,
        interval_minutes=60,
        logger=log,
    )
    assert scheduler is None
    log.info.assert_not_called()


@patch("app.jobs.deadline_reminder_scheduler.AsyncIOScheduler")
def test_scheduler_started_when_enabled(mock_cls):
    log = MagicMock()
    instance = MagicMock()
    mock_cls.return_value = instance

    result = start_deadline_reminder_scheduler(
        enabled=True,
        allow_db_failure=False,
        interval_minutes=90,
        logger=log,
    )

    mock_cls.assert_called_once()
    instance.add_job.assert_called_once()
    args, kwargs = instance.add_job.call_args
    assert args[0] is run_deadline_reminder_scan
    assert kwargs["id"] == "deadline_reminder_scan"
    assert kwargs["replace_existing"] is True
    instance.start.assert_called_once()
    log.info.assert_called_once_with(
        "deadline_reminder_scheduler_started",
        interval_minutes=90,
    )
    assert result is instance
