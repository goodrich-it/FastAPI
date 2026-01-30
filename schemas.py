from pydantic import BaseModel
from typing import Optional, List, Any, Literal


# =========================
# WHERE CONDITION
# =========================
class QueryWhere(BaseModel):
    field: str
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "like", "between"]
    value: Any


# =========================
# QUERY PLAN (NON-AGGREGATE)
# =========================
class QueryPlan(BaseModel):
    table: str
    select: Optional[List[str]] = None
    where: Optional[List[QueryWhere]] = []
    joins: list[str] | None = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0
    order_by: Optional[str] = None
    order_dir: Optional[Literal["ASC", "DESC"]] = "DESC"


# =========================
# METRIC (REPORT)
# =========================
class Metric(BaseModel):
    """
    type:
    - count  -> COUNT(*)
    - sum    -> SUM(field)
    - avg    -> AVG(field)
    """
    type: Literal["count", "sum", "avg"]
    field: Optional[str] = None  # count boleh None
    alias: str


# =========================
# REPORT PLAN
# =========================
class ReportPlan(BaseModel):
    table: str
    metrics: List[Metric]
    where: Optional[List[QueryWhere]] = []
    group_by: Optional[str] = None


# =========================
# LLM RESPONSE
# =========================
class LLMResponse(BaseModel):
    intent: Literal["chat", "query", "report"]
    query_plan: Optional[dict] = None
    reply: Optional[str] = ""


# =========================
# CHAT REQUEST
# =========================
class ChatRequest(BaseModel):
    message: str
