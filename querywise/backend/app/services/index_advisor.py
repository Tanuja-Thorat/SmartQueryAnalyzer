"""
Index Advisor

Parses a SQL query to find:
  - the main table(s) referenced
  - columns used in WHERE, JOIN, ORDER BY, GROUP BY

Then checks existing indexes on those tables (via pg_indexes) and, if a
useful index doesn't already exist, generates a recommended CREATE INDEX
statement with a plain-English reason.

This is a heuristic, regex/sqlparse based advisor - not a full SQL parser.
It is intentionally conservative: if it isn't confident about a column, it
skips it rather than recommending a bad index.
"""
import re
from typing import Dict, List, Set

import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Comparison
from sqlparse.tokens import Keyword, DML

from app.database import get_target_connection


def _extract_tables(parsed) -> List[str]:
    """Very simple FROM/JOIN table extractor."""
    tables = []
    tokens = list(parsed.flatten())
    text = parsed.value

    # FROM <table>
    from_match = re.search(r"\bFROM\s+([a-zA-Z_][\w\.]*)", text, re.IGNORECASE)
    if from_match:
        tables.append(from_match.group(1).split(".")[-1])

    # JOIN <table>
    for m in re.finditer(r"\bJOIN\s+([a-zA-Z_][\w\.]*)", text, re.IGNORECASE):
        tables.append(m.group(1).split(".")[-1])

    # de-duplicate, preserve order
    seen: Set[str] = set()
    result = []
    for t in tables:
        if t.lower() not in seen:
            seen.add(t.lower())
            result.append(t)
    return result


def _extract_where_columns(text: str) -> List[str]:
    """Find column names used in WHERE conditions (col = / > / < / IN / LIKE)."""
    where_match = re.search(
        r"\bWHERE\b(.*?)(\bGROUP BY\b|\bORDER BY\b|\bLIMIT\b|$)",
        text, re.IGNORECASE | re.DOTALL,
    )
    if not where_match:
        return []
    where_clause = where_match.group(1)

    columns = []
    # column_name <op> value   OR   column_name IN (...)  OR column_name LIKE
    for m in re.finditer(
        r"([a-zA-Z_][\w]*\.)?([a-zA-Z_][\w]*)\s*(=|<|>|<=|>=|<>|!=|IN|LIKE)\s",
        where_clause, re.IGNORECASE,
    ):
        col = m.group(2)
        if col.upper() not in ("AND", "OR", "NOT"):
            columns.append(col)
    return list(dict.fromkeys(columns))  # de-duplicate, preserve order


def _extract_order_by_columns(text: str) -> List[str]:
    m = re.search(r"\bORDER BY\b(.*?)(\bLIMIT\b|$)", text, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    clause = m.group(1)
    columns = []
    for part in clause.split(","):
        part = part.strip()
        col = re.split(r"\s+", part)[0]
        col = col.split(".")[-1]
        if col:
            columns.append(re.sub(r"[^\w]", "", col))
    return [c for c in columns if c]


def _extract_group_by_columns(text: str) -> List[str]:
    m = re.search(r"\bGROUP BY\b(.*?)(\bORDER BY\b|\bLIMIT\b|\bHAVING\b|$)", text, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    clause = m.group(1)
    columns = []
    for part in clause.split(","):
        part = part.strip().split(".")[-1]
        part = re.sub(r"[^\w]", "", part)
        if part:
            columns.append(part)
    return columns


def _extract_join_columns(text: str) -> List[str]:
    """Find columns used in ON clauses of JOINs."""
    columns = []
    for m in re.finditer(r"\bON\b\s*([a-zA-Z_][\w\.]*)\s*=\s*([a-zA-Z_][\w\.]*)", text, re.IGNORECASE):
        for side in (m.group(1), m.group(2)):
            columns.append(side.split(".")[-1])
    return list(dict.fromkeys(columns))


def analyze_query_columns(query_text: str) -> Dict[str, List[str]]:
    """Returns a dict describing tables and relevant columns found in the query."""
    parsed = sqlparse.parse(query_text)[0]
    tables = _extract_tables(parsed)

    return {
        "tables": tables,
        "where_columns": _extract_where_columns(query_text),
        "order_by_columns": _extract_order_by_columns(query_text),
        "group_by_columns": _extract_group_by_columns(query_text),
        "join_columns": _extract_join_columns(query_text),
    }


def get_existing_indexes(table_name: str) -> List[Dict]:
    """Fetch existing indexes for a table from pg_indexes."""
    sql = """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = %s
    """
    try:
        with get_target_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (table_name,))
                return [dict(row) for row in cur.fetchall()]
    except Exception:
        # If we can't inspect indexes (e.g. table doesn't exist), fail soft.
        return []


def _columns_already_indexed(existing_indexes: List[Dict], columns: List[str]) -> bool:
    """Rough check: does any existing index already cover this exact leading column set?"""
    if not columns:
        return False
    target = columns[0].lower()
    for idx in existing_indexes:
        indexdef = idx.get("indexdef", "").lower()
        # crude match: does the index definition mention the first column right after '('
        m = re.search(r"\(([^)]*)\)", indexdef)
        if m:
            idx_cols = [c.strip().split(" ")[0] for c in m.group(1).split(",")]
            if idx_cols and idx_cols[0] == target:
                return True
    return False


def generate_index_recommendations(query_text: str, has_seq_scan: bool) -> List[Dict]:
    """
    Main entry point. Analyzes the query, checks existing indexes, and
    returns a list of recommendation dicts:
      { table, columns, index_sql, reason, estimated_improvement }
    """
    info = analyze_query_columns(query_text)
    recommendations = []

    if not info["tables"]:
        return recommendations

    # We focus the recommendation on the primary (first) table referenced,
    # which is the most common and safest case for a beginner-friendly tool.
    table = info["tables"][0]
    existing_indexes = get_existing_indexes(table)

    # Build the candidate column list: WHERE columns first (most selective),
    # then ORDER BY / GROUP BY / JOIN columns as secondary composite columns.
    candidate_columns: List[str] = []
    for col in info["where_columns"] + info["join_columns"]:
        if col not in candidate_columns:
            candidate_columns.append(col)

    secondary_columns: List[str] = []
    for col in info["order_by_columns"] + info["group_by_columns"]:
        if col not in candidate_columns and col not in secondary_columns:
            secondary_columns.append(col)

    if not candidate_columns and not secondary_columns:
        return recommendations

    final_columns = (candidate_columns or secondary_columns[:1]) + (
        secondary_columns if candidate_columns else []
    )
    # de-duplicate while preserving order
    final_columns = list(dict.fromkeys(final_columns))[:3]  # cap composite width at 3

    if not final_columns:
        return recommendations

    if _columns_already_indexed(existing_indexes, final_columns):
        # Don't recommend a duplicate index
        return recommendations

    index_name = f"idx_{table}_{'_'.join(final_columns)}"
    index_name = re.sub(r"[^\w]", "_", index_name)[:63]  # Postgres identifier limit
    columns_sql = ", ".join(final_columns)
    index_sql = f"CREATE INDEX {index_name} ON {table}({columns_sql});"

    reason_parts = []
    if candidate_columns:
        reason_parts.append(
            f"The query filters and/or joins on {', '.join(candidate_columns)}."
        )
    if secondary_columns:
        reason_parts.append(
            f"It also sorts/groups by {', '.join(secondary_columns)}."
        )
    reason_parts.append(
        "A composite index on these columns can reduce sequential scanning "
        "and avoid expensive sort operations." if has_seq_scan else
        "An index on these columns can further improve lookup and sort performance."
    )
    reason = " ".join(reason_parts)

    # Simple heuristic for estimated improvement, refined later by the simulator
    estimated_improvement = 55 if has_seq_scan else 25

    recommendations.append({
        "table": table,
        "columns": final_columns,
        "index_sql": index_sql,
        "reason": reason,
        "estimated_improvement": estimated_improvement,
    })

    return recommendations
