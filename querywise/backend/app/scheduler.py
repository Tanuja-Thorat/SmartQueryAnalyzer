"""
Simple background scheduler.

Periodically scans stored query analyses and (re)flags any that cross the
slow-query threshold. This is intentionally simple: no external task queue,
just APScheduler running inside the FastAPI process.
"""
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.models.models import QueryAnalysis

logger = logging.getLogger("querywise.scheduler")

SLOW_QUERY_THRESHOLD_MS = float(os.getenv("SLOW_QUERY_THRESHOLD_MS", "500"))


def check_slow_queries():
    """Re-evaluate stored analyses against the current slow-query threshold."""
    db = SessionLocal()
    try:
        rows = db.query(QueryAnalysis).filter(
            QueryAnalysis.execution_time.isnot(None)
        ).all()

        updated = 0
        for row in rows:
            should_be_slow = 1 if row.execution_time >= SLOW_QUERY_THRESHOLD_MS else 0
            if row.is_slow != should_be_slow:
                row.is_slow = should_be_slow
                updated += 1

        if updated:
            db.commit()
            logger.info("Slow query scan: updated %d records", updated)
    except Exception as e:
        logger.warning("Slow query scan failed: %s", e)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    # Run every 5 minutes - simple interval, no need for cron complexity here
    scheduler.add_job(check_slow_queries, "interval", minutes=5, id="slow_query_scan")
    scheduler.start()
    logger.info("Background scheduler started (slow query scan every 5 minutes)")
    return scheduler
