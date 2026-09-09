from fastapi import APIRouter, HTTPException

from app.services import db_explorer

router = APIRouter(prefix="/api/explorer", tags=["explorer"])


@router.get("/tables")
def list_tables():
    """List every table in the target database with its live row count."""
    try:
        tables = db_explorer.list_tables_with_counts()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to the target database. Check your database is running and .env is configured correctly.",
        )
    return {"success": True, "tables": tables, "total_tables": len(tables)}


@router.get("/tables/{table_name}")
def table_detail(table_name: str):
    """Columns, primary key, foreign keys, and indexes for one table."""
    try:
        detail = db_explorer.get_table_detail(table_name)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to the target database. Check your database is running and .env is configured correctly.",
        )
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' was not found in the database.")
    return {"success": True, **detail}


@router.get("/schema")
def get_schema():
    """Returns the full schema (all tables, columns, keys) for ER diagrams."""
    try:
        schema = db_explorer.get_full_schema()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to the target database. Check your database is running and .env is configured correctly.",
        )
    return {"success": True, "schema": schema}
