"""
Health Score

Converts a parsed execution plan into a 0-100 "query health score" using
simple, explainable heuristics (no ML - just readable rules a beginner can
follow and tweak).
"""
from typing import Dict, List, Tuple


def _status_for_score(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 40:
        return "Needs Improvement"
    return "Poor"


def calculate_health_score(explain_summary: Dict, node_types: List[str]) -> Tuple[int, str, List[str]]:
    """
    Returns (score, status, issues).

    Deductions (start at 100, subtract for each problem found):
      - Sequential scan present:            -20
      - Very high total cost (>1000):        -20
      - Moderately high total cost (>200):   -10
      - Large estimated row count (>10000):  -15
      - Sort operation present:               -5
      - Nested Loop with high cost:          -10
      - Hash Join present (mild):             -5 (informational, joins aren't bad by default)
      - No index-related scan at all:        -10 (encourages index usage)
    """
    score = 100
    issues: List[str] = []

    total_cost = explain_summary.get("total_cost", 0)
    estimated_rows = explain_summary.get("estimated_rows", 0)

    if "Seq Scan" in node_types:
        score -= 20
        issues.append(
            "Sequential scan detected — PostgreSQL is reading most/all rows "
            "of a table instead of using an index."
        )

    if total_cost > 1000:
        score -= 20
        issues.append(f"Very high query cost ({total_cost}) reported by the planner.")
    elif total_cost > 200:
        score -= 10
        issues.append(f"Moderately high query cost ({total_cost}) reported by the planner.")

    if estimated_rows > 10000:
        score -= 15
        issues.append(
            f"The planner estimates a large number of rows will be scanned "
            f"({estimated_rows} rows)."
        )

    if "Sort" in node_types:
        score -= 5
        issues.append(
            "An expensive Sort operation was found. Consider an index that "
            "matches your ORDER BY columns to avoid sorting in memory/disk."
        )

    if "Nested Loop" in node_types and total_cost > 200:
        score -= 10
        issues.append(
            "A costly Nested Loop join was detected — this can be slow when "
            "joining large tables without proper indexes."
        )

    if "Hash Join" in node_types:
        score -= 5
        issues.append(
            "A Hash Join was used. This is often fine, but can be costly on "
            "very large tables."
        )

    has_index_scan = any(
        t in node_types for t in ("Index Scan", "Index Only Scan", "Bitmap Heap Scan")
    )
    if not has_index_scan and "Seq Scan" in node_types:
        score -= 10
        issues.append("No index scans were used anywhere in this query plan.")

    score = max(0, min(100, score))
    status = _status_for_score(score)

    if not issues:
        issues.append("No major performance issues detected. Great job!")

    return score, status, issues
