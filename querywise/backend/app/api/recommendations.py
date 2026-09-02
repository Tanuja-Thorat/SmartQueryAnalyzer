from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import IndexRecommendation, QueryAnalysis, Query
from app.schemas.schemas import SimulateIndexRequest, SimulateIndexResponse
from app.services.query_analyzer import analyze_query, QueryAnalysisError
from app.services.index_simulator import simulate_index

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db)):
    rows = (
        db.query(IndexRecommendation)
        .options(joinedload(IndexRecommendation.analysis).joinedload(QueryAnalysis.query))
        .order_by(IndexRecommendation.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": r.id,
            "table": r.table_name,
            "columns": r.columns,
            "index_sql": r.recommended_index_sql,
            "reason": r.reason,
            "estimated_improvement": r.estimated_improvement,
            "status": r.status,
            "query_text": r.analysis.query.query_text if r.analysis and r.analysis.query else "",
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/simulate-index", response_model=SimulateIndexResponse)
def simulate(payload: SimulateIndexRequest):
    """
    Runs a safe what-if simulation for a proposed index. Never creates the
    index in the real database.
    """
    if not payload.index_sql.strip().upper().startswith("CREATE INDEX"):
        raise HTTPException(
            status_code=400,
            detail="Only CREATE INDEX statements can be simulated.",
        )

    try:
        analysis = analyze_query(payload.query, run_analyze=False)
    except QueryAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))

    has_seq_scan = analysis["scan_type"] == "Seq Scan"
    result = simulate_index(
        payload.query,
        payload.index_sql,
        {
            "total_cost": analysis["total_cost"],
            "estimated_rows": analysis["estimated_rows"],
        },
        has_seq_scan,
    )

    return SimulateIndexResponse(
        success=True,
        original_cost=result["original_cost"],
        estimated_optimized_cost=result["estimated_optimized_cost"],
        estimated_improvement_percent=result["estimated_improvement_percent"],
        note=result["note"],
    )
