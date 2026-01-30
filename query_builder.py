from schemas import QueryPlan, QueryWhere
from db_schema import PIPELINE_FORECASTS, CUSTOMERS

ALLOWED_TABLES = {
    "pipeline_forecasts": PIPELINE_FORECASTS,
    "customers": CUSTOMERS,
}


def build_select_query(plan: QueryPlan):
    # =====================
    # VALIDATE TABLE
    # =====================
    if plan.table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    schema = ALLOWED_TABLES[plan.table]

    # =====================
    # PREPARE ALLOWED COLUMNS
    # =====================
    allowed_columns = set(schema["columns"])

    if plan.joins:
        if "relations" not in schema:
            raise ValueError("This table does not support joins")

        for join_key in plan.joins:
            if join_key not in schema["relations"]:
                raise ValueError(f"Join not allowed: {join_key}")

            rel = schema["relations"][join_key]
            for col in rel["columns"]:
                allowed_columns.add(f"{rel['table']}.{col}")

    # =====================
    # SELECT
    # =====================
    if plan.select:
        for col in plan.select:
            if col not in allowed_columns:
                raise ValueError(f"Column not allowed: {col}")
        select_sql = ", ".join(plan.select)
    else:
        select_sql = ", ".join(schema["default_columns"])

    sql = f"SELECT {select_sql} FROM {schema['table']}"
    params = []

    # =====================
    # JOIN
    # =====================
    if plan.joins:
        for join_key in plan.joins:
            rel = schema["relations"][join_key]
            sql += f" LEFT JOIN {rel['table']} ON {rel['on']}"

    # =====================
    # WHERE
    # =====================
    if plan.where:
        conditions = []

        for cond in plan.where:
            if cond.field not in allowed_columns:
                raise ValueError(f"Where column not allowed: {cond.field}")

            conditions.append(f"{cond.field} {cond.operator} %s")
            params.append(cond.value)

        sql += " WHERE " + " AND ".join(conditions)

    # =====================
    # ORDER BY
    # =====================
    if plan.order_by:
        if plan.order_by not in allowed_columns:
            raise ValueError("Order by column not allowed")

        sql += f" ORDER BY {plan.order_by} {plan.order_dir}"

    # =====================
    # LIMIT & OFFSET
    # =====================
    sql += " LIMIT %s OFFSET %s"
    params.extend([plan.limit, plan.offset])

    # =====================
    # DEBUG
    # =====================
    print("===== QUERY SQL =====")
    print(sql)
    print("===== PARAMS =====")
    print(params)

    return sql, params
