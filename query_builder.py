from schemas import QueryPlan
from db_schema import PIPELINE_FORECASTS, CUSTOMERS


ALLOWED_TABLES = {
    "pipeline_forecasts": PIPELINE_FORECASTS,
    "customers": CUSTOMERS,
}


def normalize_column(col: str):
    """
    Remove alias if exist:
    'customers.name AS customer_name'
    -> customers.name
    """
    return col.split(" AS ")[0].strip()


def build_select_query(plan: QueryPlan):

    if plan.table not in ALLOWED_TABLES:
        raise ValueError("Table not allowed")

    schema = ALLOWED_TABLES[plan.table]

    allowed_columns = set(f"{schema['table']}.{c}" for c in schema["columns"])

    # =====================
    # JOIN
    # =====================
    join_sql = ""

    if plan.joins:
        if "relations" not in schema:
            raise ValueError("Join not supported")

        for join_key in plan.joins:

            # if join_key not in schema["relations"]:
            #     raise ValueError(f"Join not allowed: {join_key}")

            rel = schema["relations"][join_key]

            join_sql += f" LEFT JOIN {rel['table']} ON {rel['on']}"

            for col in rel["columns"]:
                allowed_columns.add(f"{rel['table']}.{col}")

    # =====================
    # SELECT
    # =====================
    if plan.select:

        select_parts = []

        for col in plan.select:
            base_col = normalize_column(col)

            # if base_col not in allowed_columns:
            #     raise ValueError(f"Column not allowed: {col}")

            select_parts.append(col)

        select_sql = ", ".join(select_parts)

    else:
        select_sql = ", ".join(schema["default_columns"])

    sql = f"SELECT {select_sql} FROM {schema['table']}"
    sql += join_sql

    params = []

    # =====================
    # WHERE
    # =====================
    if plan.where:

        conditions = []

        for cond in plan.where:

            # if cond.field not in allowed_columns:
            #     raise ValueError(f"Where column not allowed: {cond.field}")

            op = cond.operator.lower()

            if op == "between":
                conditions.append(f"{cond.field} BETWEEN %s AND %s")
                params.extend(cond.value)

            else:
                conditions.append(f"{cond.field} {cond.operator} %s")
                params.append(cond.value)

        sql += " WHERE " + " AND ".join(conditions)

    # =====================
    # ORDER
    # =====================
    if plan.order_by:

        # if plan.order_by not in allowed_columns:
        #     raise ValueError("Order column not allowed")

        sql += f" ORDER BY {plan.order_by} {plan.order_dir}"

    # =====================
    # LIMIT OFFSET
    # =====================
    sql += " LIMIT %s OFFSET %s"
    params.extend([plan.limit, plan.offset])

    print("===== QUERY SQL =====")
    print(sql)
    print("===== PARAMS =====")
    print(params)

    return sql, params
