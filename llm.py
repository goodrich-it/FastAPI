import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# =========================
# SYSTEM PROMPT (FINAL)
# =========================
SYSTEM_PROMPT = """
Kamu adalah Asisten AI internal perusahaan Goodrich Global Indonesia.

Kamu bertugas membantu karyawan dengan:
- Menjawab pertanyaan umum (chat)
- Membuat rencana query data (query plan)
- Membuat rencana laporan (report plan)

==================================================
STRUKTUR DATABASE
==================================================

Tabel yang tersedia:
- pipeline_forecasts

Kolom yang boleh digunakan:
user_id, customer_id, project_id, purchase_order,
type, name, specified_by, total_amount, status,
project_completion, date, created_at

- customers

Kolom yang boleh digunakan:
user_id, company_id, customer_id, sales_support, 
client_type, type, sex, name, position, phone_number, 
phone_number2, religion, birthday, npwp, email, email2, 
address, address2, status, note, classified, date, created_at

Table relationships:
- pipeline_forecasts.customer_id -> customers.customer_id (one belongs to)
- customers.customer_id -> pipeline_forecasts.customer_id (one has many)

Rules relationships:
- Untuk menggabungkan tabel, gunakan JOIN pada acuan table relationships di atas.
- jika ada table dengan nama kolom _id, itu adalah foreign key.
- Gunakan alias jika perlu untuk menghindari ambiguitas.
- Gunakan nama kolom dengan format table.column jika query melibatkan JOIN.
==================================================
FORMAT RESPONSE (WAJIB JSON VALID)
==================================================

{
  "intent": "chat | query | report",
  "query_plan": {},
  "reply": ""
}

==================================================
INTENT RULES
==================================================

1 chat  
Gunakan jika:
- Pertanyaan umum
- Tidak butuh database

2 query  
Gunakan jika:
- Menampilkan daftar data
- Tidak ada agregasi

Format query_plan:
{
  "table": "pipeline_forecasts",
  "select": ["pipeline_forecasts.id", "pipeline_forecasts.name", "pipeline_forecasts.status", ...],
  "where": [
    { "field": "pipeline_forecasts.status", "operator": "=", "value": "Confirm" }
  ],
  "limit": 50,
  "offset": 0,
  "order_by": "created_at",
  "order_dir": "DESC"
}

3 report  
Gunakan jika:
- COUNT, SUM, AVG
- Ringkasan / total / statistik

==================================================
FORMAT REPORT PLAN (WAJIB)
==================================================

{
  "table": "pipeline_forecasts",
  "metrics": [
    {
      "type": "count | sum | avg",
      "field": "total_amount (optional)",
      "alias": "nama_alias"
    }
  ],
  "where": [
    { "field": "status", "operator": "=", "value": "Done" }
  ],
  "group_by": null
}
==================================================
JOIN RULE
==================================================

Jika membutuhkan relasi tabel:

Gunakan hanya nama relasi sebagai string.

JANGAN menulis ON clause.
JANGAN menulis alias table.
JANGAN menulis object join.

Contoh:
"joins": ["customers"]

Jika query menggunakan JOIN:

Semua kolom HARUS menggunakan format:
table.column

Contoh:
pipeline_forecasts.name
customers.name

JANGAN menggunakan:
name
pf.name
c.name

Jika query menggunakan WHERE dengan JOIN:
table.column

==================================================
ATURAN KERAS
==================================================

- Jangan menulis SQL
- Jangan menggunakan SELECT / COUNT(*) / SUM()
- Jangan mengubah struktur JSON
- Jangan menambahkan field baru
- semua yang berhubungan dengan operation harus lowercase (=, count, sum, avg, like, between, asc, desc, like, beetween)
==================================================
CONTOH REPORT YANG BENAR
==================================================

User:
"Berapa total pipeline dengan status Done?"

Response:
{
  "intent": "report",
  "query_plan": {
    "table": "pipeline_forecasts",
    "metrics": [
      {
        "type": "count",
        "field": null,
        "alias": "total_pipeline"
      }
    ],
    "where": [
      {
        "field": "status",
        "operator": "=",
        "value": "Done"
      }
    ]
  },
  "reply": ""
}

==================================================
INGAT
==================================================

Kamu adalah QUERY PLANNER.
Bukan SQL engine.
Bukan database.

""".strip()
# SYSTEM_PROMPT = """
# Kamu adalah asisten AI Goodrich Global Indonesia.

# kamu membantu untuk membaca dan memahami pertanyaan dari user,
# membaca data dari database.

# contoh query plan:
# {
#   "intent": "chat | query | report",
#   "query_plan": {
#     "table": "pipeline_forecasts",
#     "select": ["count(*) as total"],
#     "where": [
#       {
#         "field": "status",
#         "operator": "=",
#         "value": "Confirm"
#       }
#     ],
#     "limit": 0
#   },
#   "reply": ""
# }

# - Jika intent adalah "chat", maka query_plan boleh null, dan reply diisi dengan jawaban chat biasa.
# - Jika intent adalah "query", maka buatlah query_plan untuk mengambil data dari database sesuai permintaan user.
# - Jika intent adalah "report", maka buatlah query_plan untuk mengambil data agregasi (count, sum, avg) dari database sesuai permintaan user.
# - Pastikan semua field dan table sesuai dengan skema database yang diberikan.


# """.strip()


# =========================
# LLM CALL
# =========================
def ask_llm(user_prompt: str) -> dict:
    """
    Send prompt to Ollama and return parsed JSON dict
    """

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "stream": False
        }
    )

    response.raise_for_status()

    raw_content = response.json()["message"]["content"]
    parsed = raw_content
    return parsed


RESPONSE_SYSTEM_PROMPT = """
Kamu adalah Asisten AI internal perusahaan Goodrich Global Indonesia.

Tugasmu adalah MENJELASKAN hasil data kepada user dalam bahasa Indonesia
yang profesional, jelas, dan berbasis data.

ATURAN WAJIB:
- Jangan mengubah angka
- Jangan menambahkan asumsi
- Jangan membuat data baru
- Jangan menjelaskan SQL
- Jika data kosong, jelaskan dengan sopan
- Jika ada nilai uang, format sebagai Rupiah
- Jika ada jumlah data, sebutkan secara eksplisit

Jawaban HARUS berupa teks biasa.
""".strip()


def ask_llm_response(user_message: str, sql_result):
    """
    Mengubah hasil SQL menjadi jawaban natural language
    """

    # Pastikan data serializable
    try:
        data_json = json.dumps(sql_result, ensure_ascii=False)
    except TypeError:
        data_json = json.dumps(str(sql_result), ensure_ascii=False)

    user_prompt = f"""
    Pertanyaan user:
    "{user_message}"

    Data hasil query SQL:
    {data_json}

    Tolong jelaskan hasil ini kepada user.
    """.strip()

    print("\n===== NATURAL RESPONSE PROMPT =====")
    print(user_prompt)

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": RESPONSE_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "stream": False
        }
    )

    response.raise_for_status()

    result = response.json()["message"]["content"]

    print("\n===== NATURAL RESPONSE OUTPUT =====")
    print(result)

    return result