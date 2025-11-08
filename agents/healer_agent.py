# agents/healer_agent.py
from fastapi import FastAPI, Request
import sqlite3
import time
import subprocess
import requests

app = FastAPI()

DB = "agents.db"

# --- Configuration ---
PRIMARY_API = "https://api.github.com"
BACKUP_API = "https://api.gitlab.com"
CURRENT_API = PRIMARY_API  # will switch if failure detected


# --- Helper: log incidents ---
def log_incident(service, itype, detail, action, success):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO incidents (timestamp, service, type, detail, action, success) VALUES (?, ?, ?, ?, ?, ?)",
        (int(time.time()), service, itype, detail, action, 1 if success else 0),
    )
    conn.commit()
    conn.close()
    print(f"[Healer] Logged incident → {itype} | Action: {action} | Success: {success}")


# --- Helper: test if API is healthy ---
def check_api_health(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# --- Healer Endpoint ---
@app.post("/predict_event")
async def predict_event(req: Request):
    data = await req.json()
    service = data.get("service")
    etype = data.get("type")
    eta = data.get("eta_min")
    detail = data.get("detail", "No detail")

    print(f"\n[Healer] 🚨 Received prediction → {etype} for {service}, ETA: {eta}min")
    print(f"[Healer] Detail: {detail}")

    global CURRENT_API

    # Default action
    action = "No action"
    success = True

    try:
        # --- Case 1: API failures or spikes ---
        if "failure" in etype or "spike" in etype:
            print("[Healer] Checking API health...")
            if not check_api_health(PRIMARY_API):
                print("[Healer] Primary API down! Switching to backup API.")
                CURRENT_API = BACKUP_API
                action = f"Switched to backup API: {BACKUP_API}"
            else:
                print("[Healer] Primary API healthy. No switch needed.")
                action = "Checked API health (OK)."

        # --- Case 2: Slowdown detected ---
        elif "latency" in etype or "slowdown" in etype:
            print("[Healer] Attempting soft recovery: restarting local monitor.")
            subprocess.Popen(["python", "-m", "agents.monitor_agent"])
            action = "Restarted monitor_agent to refresh metrics."

        else:
            action = "Logged prediction only."

    except Exception as e:
        success = False
        action = f"Error during healing: {e}"

    log_incident(service, etype, detail, action, success)
    return {"status": "action_taken", "action": action, "success": success}
