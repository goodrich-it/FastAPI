from typing import List
from schemas import ReportPlan, QueryWhere, Metric


def build_report_query(plan: ReportPlan):
    """
    Build SQL + params for REPORT query
    - Support count / sum / avg
    - Support where: =, >, <, >=, <=, between, in
    """

    # =========================
    # METRICS
    # =========================
    if not plan.metrics:
        raise ValueError("ReportPlan.metrics is required")

    metric_sql = []
    params: List = []

    for metric in plan.metrics:
        if metric.type == "count":
            metric_sql.append(f"COUNT(*) AS {metric.alias}")

        elif metric.type == "sum":
            if not metric.field:
                raise ValueError("SUM requires field")
            metric_sql.append(f"SUM({metric.field}) AS {metric.alias}")

        elif metric.type == "avg":
            if not metric.field:
                raise ValueError("AVG requires field")
            metric_sql.append(f"AVG({metric.field}) AS {metric.alias}")

        else:
            raise ValueError(f"Unknown metric type: {metric.type}")

    select_sql = ", ".join(metric_sql)

    # =========================
    # BASE SQL
    # =========================
    sql = f"SELECT {select_sql} FROM {plan.table}"

    # =========================
    # WHERE
    # =========================
    where_clauses = []

    for cond in plan.where or []:
        field = cond.field
        op = cond.operator.lower()
        value = cond.value

        # ---- BETWEEN ----
        if op == "between":
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("BETWEEN requires list with 2 values")

            where_clauses.append(f"{field} BETWEEN %s AND %s")
            params.extend(value)

        # ---- IN ----
        elif op == "in":
            if not isinstance(value, list) or len(value) == 0:
                raise ValueError("IN requires non-empty list")

            placeholders = ", ".join(["%s"] * len(value))
            where_clauses.append(f"{field} IN ({placeholders})")
            params.extend(value)

        # ---- NORMAL OPERATOR (=, >, <, >=, <=) ----
        else:
            where_clauses.append(f"{field} {cond.operator} %s")
            params.append(value)

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    # =========================
    # GROUP BY
    # =========================
    if plan.group_by:
        sql += f" GROUP BY {plan.group_by}"

    # =========================
    # DEBUG SAFETY CHECK
    # =========================
    for p in params:
        if isinstance(p, list):
            raise ValueError("❌ PARAM LIST DETECTED — SQL EXECUTION WILL FAIL")

    print("REPORT SQL:", sql)
    print("PARAMS:", params)

    return sql, params
