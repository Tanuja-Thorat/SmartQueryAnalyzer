from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Query, QueryAnalysis, IndexRecommendation
from app.schemas.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.query_analyzer import analyze_query, QueryAnalysisError

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    try:
        result = analyze_query(payload.query, run_analyze=payload.run_analyze)
    except QueryAnalysisError as e:
        # Friendly, safe error message only - never leak tracebacks.
        raise HTTPException(status_code=400, detail=str(e))

    # Save the query (or reuse existing record with the same hash)
    existing = db.query(Query).filter(Query.query_hash == result["query_hash"]).first()
    if existing:
        query_row = existing
    else:
        query_row = Query(query_text=result["clean_query"], query_hash=result["query_hash"])
        db.add(query_row)
        db.flush()  # get query_row.id without committing

    analysis_row = QueryAnalysis(
        query_id=query_row.id,
        total_cost=result["total_cost"],
        startup_cost=result["startup_cost"],
        estimated_rows=result["estimated_rows"],
        actual_rows=result["actual_rows"],
        execution_time=result["execution_time"],
        health_score=result["health_score"],
        health_status=result["health_status"],
        scan_type=result["scan_type"],
        is_slow=1 if result["is_slow"] else 0,
        primary_table=result["primary_table"],
        issues=result["issues"],
        plan_tree=result["plan_tree"],
        raw_plan=result["raw_plan"],
        ai_explanation=result["ai_explanation"],
    )
    db.add(analysis_row)
    db.flush()

    rec_rows = []
    for rec in result["recommendations"]:
        rec_row = IndexRecommendation(
            query_analysis_id=analysis_row.id,
            table_name=rec["table"],
            columns=rec["columns"],
            recommended_index_sql=rec["index_sql"],
            reason=rec["reason"],
            estimated_improvement=rec["estimated_improvement"],
        )
        db.add(rec_row)
        rec_rows.append(rec_row)

    db.commit()
    db.refresh(analysis_row)

    return AnalyzeResponse(
        success=True,
        query_id=query_row.id,
        analysis_id=analysis_row.id,
        health_score=result["health_score"],
        health_status=result["health_status"],
        total_cost=result["total_cost"],
        startup_cost=result["startup_cost"],
        estimated_rows=result["estimated_rows"],
        actual_rows=result["actual_rows"],
        execution_time=result["execution_time"],
        is_slow=result["is_slow"],
        scan_type=result["scan_type"],
        issues=result["issues"],
        plan_tree=result["plan_tree"],
        recommendations=[
            {
                "table": r["table"],
                "columns": r["columns"],
                "index_sql": r["index_sql"],
                "reason": r["reason"],
                "estimated_improvement": r["estimated_improvement"],
            }
            for r in result["recommendations"]
        ],
        ai_explanation=result["ai_explanation"],
    )
