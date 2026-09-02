from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.models import QueryAnalysis, IndexRecommendation
from app.schemas.schemas import (
    DashboardResponse, DashboardSummary, TrendPoint, ScanTypeCount, TableFrequency
)
from app.services import db_explorer

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    total_queries = db.query(func.count(QueryAnalysis.id)).scalar() or 0
    slow_queries = (
        db.query(func.count(QueryAnalysis.id)).filter(QueryAnalysis.is_slow == 1).scalar() or 0
    )
    avg_cost = db.query(func.avg(QueryAnalysis.total_cost)).scalar() or 0
    avg_health = db.query(func.avg(QueryAnalysis.health_score)).scalar() or 0
    total_recommendations = db.query(func.count(IndexRecommendation.id)).scalar() or 0

    # Live table count from the actual target database being analyzed.
    # Fails soft to 0 if the target DB is temporarily unreachable, so the
    # rest of the dashboard (which only needs the app DB) still loads.
    try:
        total_tables = db_explorer.get_database_summary()["total_tables"]
    except Exception:
        total_tables = 0

    summary = DashboardSummary(
        total_queries_analyzed=total_queries,
        slow_queries=slow_queries,
        average_query_cost=round(float(avg_cost), 2),
        average_health_score=round(float(avg_health), 1),
        recommended_indexes=total_recommendations,
        total_tables=total_tables,
    )

    # Trend: most recent 30 analyses, oldest first for chronological charting
    recent = (
        db.query(QueryAnalysis)
        .order_by(QueryAnalysis.created_at.desc())
        .limit(30)
        .all()
    )
    recent = list(reversed(recent))
    trend = [
        TrendPoint(
            label=row.created_at.strftime("%m/%d %H:%M") if row.created_at else f"#{row.id}",
            cost=row.total_cost,
            execution_time=row.execution_time,
            health_score=row.health_score,
            created_at=row.created_at,
        )
        for row in recent
    ]

    # Scan type distribution
    scan_rows = db.query(QueryAnalysis.scan_type).all()
    counts = Counter(r[0] or "Unknown" for r in scan_rows)
    scan_types = [ScanTypeCount(scan_type=k, count=v) for k, v in counts.most_common()]

    # Most frequently analyzed tables (top 5), based on the primary FROM
    # table detected for each analyzed query.
    table_rows = (
        db.query(QueryAnalysis.primary_table, func.count(QueryAnalysis.id))
        .filter(QueryAnalysis.primary_table.isnot(None))
        .group_by(QueryAnalysis.primary_table)
        .order_by(func.count(QueryAnalysis.id).desc())
        .limit(5)
        .all()
    )
    most_frequent_tables = [
        TableFrequency(table_name=name, times_analyzed=count) for name, count in table_rows
    ]

    return DashboardResponse(
        summary=summary,
        trend=trend,
        scan_types=scan_types,
        most_frequent_tables=most_frequent_tables,
    )
