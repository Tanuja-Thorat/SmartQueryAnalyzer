"""
Database connections.

QueryWise talks to TWO databases:

1. APP DB  -> where QueryWise stores its own data (query history, analysis
   results, index recommendations). Managed with SQLAlchemy ORM.

2. TARGET DB -> the database the user wants to analyze. We only ever run
   read-only statements (EXPLAIN, information_schema lookups) against it,
   using a raw psycopg2 connection so we have tight control over exactly
   what gets executed.
"""
import os
import contextlib
from pathlib import Path
from urllib.parse import quote_plus

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load backend/.env explicitly by absolute path (this file lives at
# backend/app/database.py, so .env is two levels up). This makes env
# loading work no matter what directory you run `uvicorn` from - a plain
# load_dotenv() only reliably finds .env when the current working
# directory happens to be `backend/`.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# ---------------------------------------------------------------------------
# APP DB (SQLAlchemy) - stores history, analysis, recommendations
# ---------------------------------------------------------------------------
APP_DB_USER = os.getenv("APP_DB_USER", "postgres")
APP_DB_PASSWORD = os.getenv("APP_DB_PASSWORD", "postgres")
APP_DB_HOST = os.getenv("APP_DB_HOST", "localhost")
APP_DB_PORT = os.getenv("APP_DB_PORT", "5432")
APP_DB_NAME = os.getenv("APP_DB_NAME", "querywise_demo")

APP_DATABASE_URL = (
    f"postgresql+psycopg2://{APP_DB_USER}:{quote_plus(APP_DB_PASSWORD)}"
    f"@{APP_DB_HOST}:{APP_DB_PORT}/{APP_DB_NAME}"
)

engine = create_engine(APP_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TARGET DB (raw psycopg2) - the database being analyzed
# ---------------------------------------------------------------------------
TARGET_DB_CONFIG = {
    "host": os.getenv("TARGET_DB_HOST", "localhost"),
    "port": os.getenv("TARGET_DB_PORT", "5432"),
    "dbname": os.getenv("TARGET_DB_NAME", "querywise_demo"),
    "user": os.getenv("TARGET_DB_USER", "postgres"),
    "password": os.getenv("TARGET_DB_PASSWORD", "postgres"),
}


@contextlib.contextmanager
def get_target_connection():
    """
    Yields a read-only-safe psycopg2 connection to the TARGET database.

    We set the session to READ ONLY at the Postgres level as a defense-in-depth
    measure, in addition to our own SQL validation layer.
    """
    conn = psycopg2.connect(cursor_factory=RealDictCursor, **TARGET_DB_CONFIG)
    try:
        conn.set_session(readonly=True, autocommit=True)
        yield conn
    finally:
        conn.close()
