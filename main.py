from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json

from db import get_connection, get_plesk_connection
from llm import ask_llm, ask_llm_response
from query_builder import build_select_query
from report_builder import build_report_query
from schemas import (
    ChatRequest,
    LLMResponse,
    QueryPlan,
    ReportPlan
)

app = FastAPI(title="AI Assistant Goodrich Global Indonesia")

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Assistant Goodrich Global Indonesia running"
    }

@app.get("/health/db")
def check_db_connection():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "error",
            "database": "failed",
            "detail": str(e)
        }

# =========================
# HEALTH - PLESK DB (SSH TUNNEL)
# =========================
@app.get("/health/db/plesk")
def check_plesk_db():
    try:
        conn = get_plesk_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()

        return {
            "status": "ok",
            "database": "plesk",
            "connected": True,
            "via": "ssh_tunnel"
        }

    except Exception as e:
        return {
            "status": "error",
            "database": "plesk",
            "connected": False,
            "detail": str(e),
            "hint": "Pastikan SSH tunnel aktif"
        }
# =========================
# CHAT (SINGLE ENTRY POINT)
# =========================
@app.post("/chat")
def chat(payload: ChatRequest):
    try:
        print("\n================ USER MESSAGE ================")
        print(payload.message)

        # =========================
        # 1️⃣ ASK LLM
        # =========================
        raw_llm_response = ask_llm(payload.message)

        print("\n===== RAW LLM RESPONSE =====")
        print(raw_llm_response)

        # =========================
        # 2️⃣ PARSE JSON
        # =========================
        if isinstance(raw_llm_response, dict):
            parsed = raw_llm_response
        else:
            parsed = json.loads(raw_llm_response)

        print("\n===== PARSED LLM RESPONSE =====")
        print(parsed)

        # =========================
        # 3️⃣ VALIDATE LLM RESPONSE
        # =========================
        llm_response = LLMResponse(**parsed)
        intent = llm_response.intent

        print("\n===== INTENT =====")
        print(intent)

        # =========================
        # 4️⃣ CHAT ONLY
        # =========================
        if intent == "chat":
            return {
                "type": "chat",
                "reply": llm_response.reply
            }

        # =========================
        # DB CONNECTION
        # =========================
        conn = get_connection()
        # conn = get_plesk_connection()
        cur = conn.cursor(dictionary=True)

        # =========================
        # 5️⃣ QUERY
        # =========================
        if intent == "query":
            print("\n===== QUERY PLAN (RAW) =====")
            print(llm_response.query_plan)

            plan = QueryPlan(**llm_response.query_plan)

            print("\n===== QUERY PLAN (VALIDATED) =====")
            print(plan)

            sql, params = build_select_query(plan)

        # =========================
        # 6️⃣ REPORT
        # =========================
        elif intent == "report":
            print("\n===== REPORT PLAN (RAW) =====")
            print(llm_response.query_plan)

            plan = ReportPlan(**llm_response.query_plan)

            print("\n===== REPORT PLAN (VALIDATED) =====")
            print(plan)

            sql, params = build_report_query(plan)

        else:
            raise ValueError("Unknown intent")

        # =========================
        # EXECUTE SQL
        # =========================
        print("\n===== EXECUTE SQL =====")
        print(sql)
        print("PARAMS:", params)
        # return {
        #     "type": intent,
        #     "sql": sql,
        #     "params": params
        # }
        cur.execute(sql, params)
        rows = cur.fetchall()
        print("\n===== RESULT SQL =====")
        print(rows)
        
        cur.close()
        conn.close()

        data = rows[0] if rows else {}
        return {"data": data}
        
        final_answer = ask_llm_response(
            user_message=payload.message,
            sql_result=data
        )

        return {
            "type": intent,
            "data": rows,
            "answer": final_answer
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="LLM returned invalid JSON"
        )

    except Exception as e:
        print("\n🔥 ERROR 🔥")
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))
