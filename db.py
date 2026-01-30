import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
    )

# =========================
# PLESK DB (SSH TUNNEL)
# =========================
def get_plesk_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=int(os.getenv("PLESK_DB_TUNNEL_PORT")),
        user=os.getenv("PLESK_DB_USER"),
        password=os.getenv("PLESK_DB_PASSWORD"),
        database=os.getenv("PLESK_DB_NAME"),
    )