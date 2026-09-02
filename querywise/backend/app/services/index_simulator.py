"""
Index Simulator (What-If Analysis)

Estimates how much a proposed index might help a query WITHOUT ever
creating a real index in the user's database.

Two strategies are used, in order of preference:

1. HypoPG (if the `hypopg` extension is installed on the target database):
   creates a *hypothetical* index that only exists for the current session
   and is never persisted or written to disk. This gives a real planner
   cost estimate. This is the "gold standard" for what-if analysis.

2. Heuristic fallback (if HypoPG isn't available): estimate improvement
   using simple rules based on the original plan (sequential scan presence,
   cost, and row counts). Clearly labeled as an estimate.
"""
from typing import Dict

from app.database import get_target_connection
from app.services.query_validator import validate_query


def _try_hypopg_simulation(query_text: str, index_sql: str) -> Dict | None:
    """Attempt a HypoPG-based simulation. Returns None if HypoPG isn't available."""
    try:
        with get_target_connection() as conn:
            with conn.cursor() as cur:
                # Check if hypopg extension exists
                cur.execute(
                    "SELECT 1 FROM pg_extension WHERE extname = 'hypopg';"
                )
                if not cur.fetchone():
                    return None

                # Original cost
                cur.execute(f"EXPLAIN (FORMAT JSON) {query_text}")
                original_plan = cur.fetchone()
                original_cost = original_plan["QUERY PLAN"][0]["Plan"]["Total Cost"]

                # Create hypothetical index (session-only, never persisted)
                cur.execute("SELECT hypopg_create_index(%s);", (index_sql,))

                # Cost with hypothetical index
                cur.execute(f"EXPLAIN (FORMAT JSON) {query_text}")
                new_plan = cur.fetchone()
                new_cost = new_plan["QUERY PLAN"][0]["Plan"]["Total Cost"]

                # Clean up hypothetical indexes for this session
                cur.execute("SELECT hypopg_reset();")

                improvement = 0.0
                if original_cost > 0:
                    improvement = max(0.0, (original_cost - new_cost) / original_cost * 100)

                return {
                    "original_cost": round(original_cost, 2),
                    "estimated_optimized_cost": round(new_cost, 2),
                    "estimated_improvement_percent": round(improvement, 1),
                    "method": "hypopg",
                }
    except Exception:
        return None


def _heuristic_simulation(explain_summary: Dict, has_seq_scan: bool) -> Dict:
    """
    Fallback heuristic when HypoPG is unavailable.

    Rules of thumb (rough industry heuristics, not guarantees):
      - Sequential scan -> assume an index scan could cut cost significantly,
        scaled by how large the estimated row count is.
      - No sequential scan -> assume a more modest improvement from a better
        composite index (helps sorting/joins).
    """
    original_cost = explain_summary.get("total_cost", 0) or 1
    estimated_rows = explain_summary.get("estimated_rows", 0)

    if has_seq_scan:
        # Larger tables benefit more from moving off a seq scan
        if estimated_rows > 10000:
            reduction_ratio = 0.75
        elif estimated_rows > 1000:
            reduction_ratio = 0.65
        else:
            reduction_ratio = 0.45
    else:
        reduction_ratio = 0.20

    new_cost = original_cost * (1 - reduction_ratio)
    improvement = reduction_ratio * 100

    return {
        "original_cost": round(original_cost, 2),
        "estimated_optimized_cost": round(new_cost, 2),
        "estimated_improvement_percent": round(improvement, 1),
        "method": "heuristic",
    }


def simulate_index(query_text: str, index_sql: str, explain_summary: Dict, has_seq_scan: bool) -> Dict:
    """
    Runs a safe what-if simulation for a proposed index.
    Never modifies the real database - either uses HypoPG's session-local
    hypothetical indexes, or falls back to a heuristic estimate.
    """
    query_text = validate_query(query_text)

    hypopg_result = _try_hypopg_simulation(query_text, index_sql)
    if hypopg_result:
        result = hypopg_result
    else:
        result = _heuristic_simulation(explain_summary, has_seq_scan)

    result["note"] = (
        "This is an ESTIMATE based on the PostgreSQL planner"
        + (" using HypoPG hypothetical indexes." if result["method"] == "hypopg"
           else " and heuristic rules (HypoPG extension not detected).")
        + " No index was created and your database was not modified. "
          "Actual performance may vary."
    )
    return result
