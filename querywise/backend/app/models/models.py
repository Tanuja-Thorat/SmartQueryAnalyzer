"""SQLAlchemy ORM models for the QueryWise app database."""
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Query(Base):
    """A unique SQL query submitted for analysis."""
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    analyses = relationship(
        "QueryAnalysis", back_populates="query", cascade="all, delete-orphan"
    )


class QueryAnalysis(Base):
    """Result of running EXPLAIN on a query at a point in time."""
    __tablename__ = "query_analysis"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)

    total_cost = Column(Float, default=0)
    startup_cost = Column(Float, default=0)
    estimated_rows = Column(Integer, default=0)
    actual_rows = Column(Integer, nullable=True)
    execution_time = Column(Float, nullable=True)  # milliseconds

    health_score = Column(Integer, default=0)
    health_status = Column(String(32), default="Unknown")

    scan_type = Column(String(64), nullable=True)  # e.g. "Seq Scan", "Index Scan"
    is_slow = Column(Integer, default=0)  # 0/1 boolean flag
    primary_table = Column(String(128), nullable=True, index=True)  # main FROM table, for dashboard stats

    issues = Column(JSON, default=list)         # list[str]
    plan_tree = Column(JSON, default=dict)       # simplified plan tree for UI
    raw_plan = Column(JSON, default=dict)         # raw EXPLAIN JSON (debug)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    query = relationship("Query", back_populates="analyses")
    recommendations = relationship(
        "IndexRecommendation", back_populates="analysis",
        cascade="all, delete-orphan"
    )


class IndexRecommendation(Base):
    """A suggested index derived from a query analysis."""
    __tablename__ = "index_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    query_analysis_id = Column(Integer, ForeignKey("query_analysis.id"), nullable=False)

    table_name = Column(String(128), nullable=False)
    columns = Column(JSON, default=list)  # list[str]
    recommended_index_sql = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    estimated_improvement = Column(Float, default=0)  # percentage

    status = Column(String(32), default="suggested")  # suggested / dismissed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    analysis = relationship("QueryAnalysis", back_populates="recommendations")
