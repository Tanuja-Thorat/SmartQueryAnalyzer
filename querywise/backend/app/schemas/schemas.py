"""Pydantic request/response schemas."""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    query: str = Field(..., description="A read-only SELECT SQL query")
    run_analyze: bool = Field(
        False, description="If true, run EXPLAIN ANALYZE (actually executes the query)"
    )


class IndexRecommendationOut(BaseModel):
    table: str
    columns: List[str]
    index_sql: str
    reason: str
    estimated_improvement: float

    class Config:
        from_attributes = True


class PlanNodeOut(BaseModel):
    operation: str
    cost: float
    rows: int
    warning_level: str  # "good" | "warning" | "critical"
    detail: Optional[str] = None
    children: List["PlanNodeOut"] = []


PlanNodeOut.model_rebuild()


class AnalyzeResponse(BaseModel):
    success: bool
    query_id: int
    analysis_id: int
    health_score: int
    health_status: str
    total_cost: float
    startup_cost: float
    estimated_rows: int
    actual_rows: Optional[int] = None
    execution_time: Optional[float] = None
    is_slow: bool
    scan_type: Optional[str] = None
    issues: List[str]
    plan_tree: Optional[PlanNodeOut] = None
    recommendations: List[IndexRecommendationOut]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
class SimulateIndexRequest(BaseModel):
    query: str
    index_sql: str


class SimulateIndexResponse(BaseModel):
    success: bool
    original_cost: float
    estimated_optimized_cost: float
    estimated_improvement_percent: float
    note: str


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
class HistoryItem(BaseModel):
    analysis_id: int
    query_id: int
    query_text: str
    total_cost: float
    execution_time: Optional[float]
    health_score: int
    health_status: str
    is_slow: bool
    issues: List[str]
    recommendation_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryDetail(HistoryItem):
    startup_cost: float
    estimated_rows: int
    actual_rows: Optional[int]
    scan_type: Optional[str]
    plan_tree: Optional[Dict[str, Any]]
    recommendations: List[IndexRecommendationOut]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardSummary(BaseModel):
    total_queries_analyzed: int
    slow_queries: int
    average_query_cost: float
    average_health_score: float
    recommended_indexes: int
    total_tables: int = 0


class TrendPoint(BaseModel):
    label: str
    cost: float
    execution_time: Optional[float]
    health_score: int
    created_at: datetime


class ScanTypeCount(BaseModel):
    scan_type: str
    count: int


class TableFrequency(BaseModel):
    table_name: str
    times_analyzed: int


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    trend: List[TrendPoint]
    scan_types: List[ScanTypeCount]
    most_frequent_tables: List[TableFrequency] = []


# ---------------------------------------------------------------------------
# Database Explorer
# ---------------------------------------------------------------------------
class ExplorerTableSummary(BaseModel):
    table_name: str
    row_count: int


class ExplorerTablesResponse(BaseModel):
    success: bool
    tables: List[ExplorerTableSummary]
    total_tables: int


class ExplorerColumn(BaseModel):
    column_name: str
    data_type: str
    is_nullable: str
    column_default: Optional[str] = None


class ExplorerForeignKey(BaseModel):
    column_name: str
    referenced_table: str
    referenced_column: str


class ExplorerIndex(BaseModel):
    indexname: str
    indexdef: str


class ExplorerTableDetailResponse(BaseModel):
    success: bool
    table_name: str
    row_count: int
    columns: List[ExplorerColumn]
    primary_keys: List[str]
    foreign_keys: List[ExplorerForeignKey]
    indexes: List[ExplorerIndex]
