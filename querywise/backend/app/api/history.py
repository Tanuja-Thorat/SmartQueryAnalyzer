from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import Query, QueryAnalysis
from app.schemas.schemas import HistoryItem, HistoryDetail

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=list[HistoryItem])
def get_history(
    db: Session = Depends(get_db),
    search: Optional[str] = QueryParam(None, description="Search within query text"),
    slow_only: bool = QueryParam(False, description="Only return slow queries"),
    limit: int = QueryParam(50, le=200),
):
    q = (
        db.query(QueryAnalysis)
        .join(Query, QueryAnalysis.query_id == Query.id)
        .options(joinedload(QueryAnalysis.query), joinedload(QueryAnalysis.recommendations))
        .order_by(QueryAnalysis.created_at.desc())
    )

    if search:
        q = q.filter(Query.query_text.ilike(f"%{search}%"))
    if slow_only:
        q = q.filter(QueryAnalysis.is_slow == 1)

    rows = q.limit(limit).all()

    return [
        HistoryItem(
            analysis_id=row.id,
            query_id=row.query_id,
            query_text=row.query.query_text,
            total_cost=row.total_cost,
            execution_time=row.execution_time,
            health_score=row.health_score,
            health_status=row.health_status,
            is_slow=bool(row.is_slow),
            issues=row.issues or [],
            recommendation_count=len(row.recommendations),
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/history/{analysis_id}", response_model=HistoryDetail)
def get_history_detail(analysis_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(QueryAnalysis)
        .options(joinedload(QueryAnalysis.query), joinedload(QueryAnalysis.recommendations))
        .filter(QueryAnalysis.id == analysis_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    return HistoryDetail(
        analysis_id=row.id,
        query_id=row.query_id,
        query_text=row.query.query_text,
        total_cost=row.total_cost,
        execution_time=row.execution_time,
        health_score=row.health_score,
        health_status=row.health_status,
        is_slow=bool(row.is_slow),
        issues=row.issues or [],
        recommendation_count=len(row.recommendations),
        created_at=row.created_at,
        startup_cost=row.startup_cost,
        estimated_rows=row.estimated_rows,
        actual_rows=row.actual_rows,
        scan_type=row.scan_type,
        plan_tree=row.plan_tree,
        recommendations=[
            {
                "table": r.table_name,
                "columns": r.columns,
                "index_sql": r.recommended_index_sql,
                "reason": r.reason,
                "estimated_improvement": r.estimated_improvement,
            }
            for r in row.recommendations
        ],
        ai_explanation=row.ai_explanation,
    )
