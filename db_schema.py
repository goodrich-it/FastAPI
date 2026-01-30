PIPELINE_FORECASTS = {
    "table": "pipeline_forecasts",
    "columns": [
        "id", "user_id", "customer_id", "project_id", "purchase_order",
        "type", "name", "specified_by", "total_amount", "status",
        "project_completion", "date", "created_at"
    ],
    "relations": {
        "customer": {
            "table": "customers",
            "on": "pipeline_forecasts.customer_id = customers.id",
            "columns": [
                "id",
                "name",
                "email",
                "phone_number",
                "company_id",
                "status"
            ]
        }
    }
}
CUSTOMERS = {
    "table": "customers",
    "columns": [
        "id","user_id","company_id","customer_id","sales_support","client_type","type","sex","name","position","phone_number","phone_number2",
        "religion","birthday","npwp","email","email2","address","address2","status","note","classified","is_transfered","cron_job","date","submission_date",
        "created_by","updated_by","created_at","updated_at",
    ]
}
