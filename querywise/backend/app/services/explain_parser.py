"""
Explain Parser

Turns PostgreSQL's raw `EXPLAIN (FORMAT JSON)` output into:
  1. A flat summary (total cost, rows, execution time, scan types found)
  2. A simplified tree structure the frontend can render as cards
"""
from typing import Any, Dict, List, Optional

# Node types we consider "expensive" or worth flagging
SCAN_WARNING_TYPES = {"Seq Scan"}
JOIN_TYPES = {"Nested Loop", "Hash Join", "Merge Join"}
SORT_TYPES = {"Sort"}
AGG_TYPES = {"Aggregate", "HashAggregate", "GroupAggregate"}

# Rough cost threshold used purely for coloring warning levels of a single node.
NODE_COST_WARNING = 100
NODE_COST_CRITICAL = 1000


def _warning_level_for_node(node: Dict[str, Any]) -> str:
    node_type = node.get("Node Type", "")
    total_cost = node.get("Total Cost", 0)

    if node_type in SCAN_WARNING_TYPES and node.get("Plan Rows", 0) and node["Plan Rows"] > 500:
        return "critical"
    if node_type in SCAN_WARNING_TYPES:
        return "warning"
    if total_cost >= NODE_COST_CRITICAL:
        return "critical"
    if total_cost >= NODE_COST_WARNING:
        return "warning"
    return "good"


def _detail_for_node(node: Dict[str, Any]) -> Optional[str]:
    parts = []
    if node.get("Relation Name"):
        parts.append(f"on {node['Relation Name']}")
    if node.get("Index Name"):
        parts.append(f"using index {node['Index Name']}")
    if node.get("Filter"):
        parts.append(f"filter: {node['Filter']}")
    if node.get("Join Type") and node.get("Node Type") in JOIN_TYPES:
        parts.append(f"({node['Join Type']} join)")
    return " ".join(parts) if parts else None


def _build_simplified_node(node: Dict[str, Any]) -> Dict[str, Any]:
    children_plans = node.get("Plans", [])
    return {
        "operation": node.get("Node Type", "Unknown"),
        "cost": round(node.get("Total Cost", 0), 2),
        "rows": node.get("Plan Rows", 0),
        "warning_level": _warning_level_for_node(node),
        "detail": _detail_for_node(node),
        "children": [_build_simplified_node(child) for child in children_plans],
    }


def _collect_node_types(node: Dict[str, Any], acc: List[str]) -> None:
    acc.append(node.get("Node Type", "Unknown"))
    for child in node.get("Plans", []):
        _collect_node_types(child, acc)


def _primary_scan_type(node_types: List[str]) -> str:
    """Pick the most 'interesting' scan type present in the plan for summary display."""
    if "Seq Scan" in node_types:
        return "Seq Scan"
    for t in ("Index Scan", "Index Only Scan", "Bitmap Heap Scan"):
        if t in node_types:
            return t
    return node_types[0] if node_types else "Unknown"


def parse_explain_output(explain_json: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parses the list returned by `EXPLAIN (FORMAT JSON) ...`.

    Returns a dict with:
      total_cost, startup_cost, estimated_rows, actual_rows, execution_time,
      scan_type, node_types (list), plan_tree (simplified dict)
    """
    if not explain_json:
        raise ValueError("Empty EXPLAIN result")

    top = explain_json[0]
    plan = top.get("Plan", {})

    node_types: List[str] = []
    _collect_node_types(plan, node_types)

    result = {
        "total_cost": round(plan.get("Total Cost", 0), 2),
        "startup_cost": round(plan.get("Startup Cost", 0), 2),
        "estimated_rows": plan.get("Plan Rows", 0),
        "actual_rows": plan.get("Actual Rows"),
        "execution_time": top.get("Execution Time"),  # only present with ANALYZE
        "planning_time": top.get("Planning Time"),
        "scan_type": _primary_scan_type(node_types),
        "node_types": node_types,
        "plan_tree": _build_simplified_node(plan),
    }
    return result
