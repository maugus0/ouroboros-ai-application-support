"""Background scan: mark approaching deadlines as reminder-recorded (integrate notifications here)."""

from app.config import settings
from app.core.logging import get_logger
from app.repositories.mysql_deadline_repo import DeadlineRepository

logger = get_logger(__name__)


async def run_deadline_reminder_scan() -> int:
    """Flag pending deadlines in the next 30 days that have not been reminded yet."""
    if settings.ALLOW_DB_FAILURE:
        return 0
    repo = DeadlineRepository()
    rows = await repo.list_pending_reminder_candidates(days=30)
    n = 0
    for row in rows:
        rid = row.get("id")
        if not rid:
            continue
        updated = await repo.mark_reminder_sent(str(rid))
        if updated:
            n += 1
            logger.info(
                "deadline_reminder_recorded",
                deadline_id=str(rid),
                user_id=row.get("user_id"),
                deadline_date=str(row.get("deadline_date")),
            )
    return n
