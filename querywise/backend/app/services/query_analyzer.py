"""
Query Analyzer

The orchestrator: takes a raw SQL string and runs it through the full
QueryWise pipeline:

  validate -> EXPLAIN -> parse plan -> health score -> index advice
"""
import hashlib
from typing import Dict

import psycopg2

from app.database import get_target_connection
from app.services.query_validator import validate_query, QueryValidationError
from app.services.explain_parser import parse_explain_output
from app.services.health_score import calculate_health_score
from app.services.index_advisor import generate_index_recommendations, analyze_query_columns

SLOW_QUERY_THRESHOLD_MS = 500


class QueryAnalysisError(Exception):
    """Raised for user-facing analysis errors (never exposes raw DB tracebacks)."""
    pass


def query_hash(query_text: str) -> str:
    return hashlib.sha256(query_text.strip().lower().encode("utf-8")).hexdigest()


def run_explain(query_text: str, run_analyze: bool = False) -> Dict:
    """
    Executes EXPLAIN (or EXPLAIN ANALYZE) on the target database and returns
    the raw JSON plan. Only ever called with a pre-validated SELECT query.
    """
    mode = "EXPLAIN (ANALYZE, FORMAT JSON, BUFFERS false)" if run_analyze else "EXPLAIN (FORMAT JSON)"
    sql = f"{mode} {query_text}"

    try:
        with get_target_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
                # psycopg2 RealDictCursor returns {'QUERY PLAN': [...]}
                return row["QUERY PLAN"]
    except psycopg2.errors.UndefinedTable:
        raise QueryAnalysisError(
            "One or more tables in your query do not exist in the database."
        )
    except psycopg2.errors.UndefinedColumn:
        raise QueryAnalysisError(
            "One or more columns in your query do not exist in the referenced table."
        )
    except psycopg2.Error:
        raise QueryAnalysisError(
            "We couldn't run this query. Please check your SQL syntax and table/column names."
        )
    except Exception:
        raise QueryAnalysisError("An unexpected error occurred while analyzing your query.")


def analyze_query(raw_query: str, run_analyze: bool = False) -> Dict:
    """
    Full analysis pipeline. Returns a dict ready to be persisted and
    serialized in the API response.
    """
    # 1. Validate
    try:
        clean_query = validate_query(raw_query)
    except QueryValidationError as e:
        raise QueryAnalysisError(str(e))

    # 2. Run EXPLAIN
    explain_json = run_explain(clean_query, run_analyze=run_analyze)

    # 3. Parse plan
    try:
        summary = parse_explain_output(explain_json)
    except Exception:
        raise QueryAnalysisError("We couldn't understand the execution plan returned by PostgreSQL.")

    node_types = summary["node_types"]
    has_seq_scan = "Seq Scan" in node_types

    # 4. Health score
    score, status, issues = calculate_health_score(summary, node_types)

    # 5. Slow query flag
    execution_time = summary.get("execution_time")
    is_slow = bool(execution_time is not None and execution_time >= SLOW_QUERY_THRESHOLD_MS)
    if is_slow:
        issues.append(
            f"This query took {round(execution_time, 1)}ms to execute, which is "
            f"above the slow query threshold of {SLOW_QUERY_THRESHOLD_MS}ms."
        )

    # 6. Index recommendations
    recommendations = generate_index_recommendations(clean_query, has_seq_scan)

    # 7. Which table this query is primarily about (for dashboard "most
    # frequently analyzed tables" stat). Best-effort - falls back to None.
    try:
        column_info = analyze_query_columns(clean_query)
        primary_table = column_info["tables"][0] if column_info["tables"] else None
    except Exception:
        primary_table = None

    return {
        "clean_query": clean_query,
        "query_hash": query_hash(clean_query),
        "primary_table": primary_table,
        "total_cost": summary["total_cost"],
        "startup_cost": summary["startup_cost"],
        "estimated_rows": summary["estimated_rows"],
        "actual_rows": summary.get("actual_rows"),
        "execution_time": execution_time,
        "scan_type": summary["scan_type"],
        "health_score": score,
        "health_status": status,
        "issues": issues,
        "is_slow": is_slow,
        "plan_tree": summary["plan_tree"],
        "raw_plan": explain_json,
        "recommendations": recommendations,
    }
