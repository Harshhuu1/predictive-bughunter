import time
import sqlite3
import requests
import numpy as np

# --- Configuration ---
DB = "agents.db"
SERVICE = "real-service"       # same name used in monitor_agent.py
WINDOW = 15                    # number of recent data points to analyze
PREDICT_URL = "http://127.0.0.1:9002/predict_event"  # healer webhook
CHECK_INTERVAL = 30            # seconds between checks

# --- Helper: fetch latest metrics from DB ---
def fetch_last_n(n=WINDOW):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT timestamp, resp_ms, err_rate FROM metrics WHERE service=? ORDER BY id DESC LIMIT ?",
        (SERVICE, n)
    )
    rows = cur.fetchall()[::-1]  # oldest → newest
    conn.close()
    return rows

# --- Core detection logic ---
def detect_anomaly(rows):
    if len(rows) < 5:
        return None

    resp_times = [r[1] for r in rows]
    err_rates = [r[2] for r in rows]

    avg_resp = np.mean(resp_times)
    std_resp = np.std(resp_times)
    avg_err = np.mean(err_rates)

    # --- Simple but powerful anomaly rules ---
    if avg_err > 0.3:
        return {
            "type": "api_failure_spike",
            "eta_min": 1,
            "confidence": 0.9,
            "message": f"High error rate detected: {avg_err*100:.1f}%"
        }

    if avg_resp > 2000 or std_resp > 1000:
        return {
            "type": "api_latency_increase",
            "eta_min": 2,
            "confidence": 0.8,
            "message": f"Response time unstable (avg={avg_resp:.1f}ms, std={std_resp:.1f}ms)"
        }

    # --- Trend-based prediction ---
    trend = np.polyfit(range(len(resp_times)), resp_times, 1)[0]  # linear slope
    if trend > 20:
        return {
            "type": "gradual_slowdown",
            "eta_min": 5,
            "confidence": 0.7,
            "message": f"API response time trending upward ({trend:.1f}ms per step)"
        }

    return None  # system healthy

# --- Notify Healer ---
def notify_healer(payload):
    try:
        r = requests.post(PREDICT_URL, json=payload, timeout=5)
        print(f"[Predictor] Sent alert → Healer [{r.status_code}] {payload['type']}")
    except Exception as e:
        print("[Predictor] Failed to notify healer:", e)

# --- Main loop ---
if __name__ == "__main__":
    print(f"[Predictor] Monitoring service '{SERVICE}' every {CHECK_INTERVAL}s...")

    while True:
        rows = fetch_last_n()
        anomaly = detect_anomaly(rows)
        if anomaly:
            notify_healer({
                "service": SERVICE,
                "type": anomaly["type"],
                "eta_min": anomaly["eta_min"],
                "confidence": anomaly["confidence"],
                "detail": anomaly["message"]
            })
        else:
            print("[Predictor] ✅ System stable.")

        time.sleep(CHECK_INTERVAL)
