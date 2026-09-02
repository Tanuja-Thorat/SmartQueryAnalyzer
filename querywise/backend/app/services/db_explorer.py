"""
Database Explorer

Read-only introspection of the TARGET database (the one being analyzed).
Lets the frontend show real table names, row counts, columns, primary/
foreign keys, and existing indexes - proving QueryWise is actually looking
at a live PostgreSQL database rather than hardcoded metadata.

Every query here is read-only (SELECT / information_schema / pg_catalog
lookups) and table names are always validated against the real table list
before being interpolated into a query, using psycopg2.sql.Identifier for
safe quoting.
"""
from typing import Dict, List, Optional

from psycopg2 import sql

from app.database import get_target_connection, TARGET_DB_CONFIG

# QueryWise's OWN bookkeeping tables (query history, analysis results,
# index recommendations). If the target database and app database happen
# to be the same physical database (the default for local/demo setups),
# these must be excluded from the Explorer / dashboard table counts -
# they aren't part of the business schema the user is analyzing.
APP_INTERNAL_TABLES = {"queries", "query_analysis", "index_recommendations"}


def get_table_names() -> List[str]:
    """All base tables in the public schema of the target database,
    excluding QueryWise's own internal bookkeeping tables."""
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    with get_target_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return [
                row["table_name"] for row in cur.fetchall()
                if row["table_name"] not in APP_INTERNAL_TABLES
            ]


def list_tables_with_counts() -> List[Dict]:
    """Table name + live row count for every table, used by the Explorer overview."""
    tables = get_table_names()
    results = []
    with get_target_connection() as conn:
        with conn.cursor() as cur:
            for table in tables:
                # table name comes only from information_schema above, so this
                # is safe - but we still use sql.Identifier for correct quoting.
                cur.execute(
                    sql.SQL("SELECT COUNT(*) AS row_count FROM {}").format(sql.Identifier(table))
                )
                count_row = cur.fetchone()
                results.append({"table_name": table, "row_count": count_row["row_count"]})
    return results


def get_database_summary() -> Dict:
    """Small summary used by the dashboard: total table count + database name."""
    tables = get_table_names()
    return {
        "total_tables": len(tables),
        "database_name": TARGET_DB_CONFIG.get("dbname"),
    }


def get_table_detail(table_name: str) -> Optional[Dict]:
    """
    Full detail for one table: columns (name/type/nullable), primary key
    columns, foreign keys (column -> referenced table.column), and existing
    indexes. Returns None if the table doesn't exist (validated first).
    """
    valid_tables = set(get_table_names())
    if table_name not in valid_tables:
        return None

    with get_target_connection() as conn:
        with conn.cursor() as cur:
            # Row count
            cur.execute(
                sql.SQL("SELECT COUNT(*) AS row_count FROM {}").format(sql.Identifier(table_name))
            )
            row_count = cur.fetchone()["row_count"]

            # Columns
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
                """,
                (table_name,),
            )
            columns = [dict(row) for row in cur.fetchall()]

            # Primary key columns
            cur.execute(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = %s
                  AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position
                """,
                (table_name,),
            )
            primary_keys = [row["column_name"] for row in cur.fetchall()]

            # Foreign keys
            cur.execute(
                """
                SELECT
                    kcu.column_name AS column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON tc.constraint_name = ccu.constraint_name
                 AND tc.table_schema = ccu.table_schema
                WHERE tc.table_schema = 'public'
                  AND tc.table_name = %s
                  AND tc.constraint_type = 'FOREIGN KEY'
                """,
                (table_name,),
            )
            foreign_keys = [dict(row) for row in cur.fetchall()]

            # Existing indexes
            cur.execute(
                "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = %s",
                (table_name,),
            )
            indexes = [dict(row) for row in cur.fetchall()]

    return {
        "table_name": table_name,
        "row_count": row_count,
        "columns": columns,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
        "indexes": indexes,
    }
