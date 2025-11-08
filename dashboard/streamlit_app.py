# dashboard/streamlit_app.py
import os
import time
import sqlite3
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

DB_PATH = "agents.db"  # local DB path (if present)
SAMPLE_POINTS = 100

st.set_page_config(page_title="Predictive Bug Hunter", layout="wide")
st.title("AI Predictive Bug Hunter & Auto-Healer Dashboard")
st.caption("Monitoring, predicting and healing. (Demo mode if no DB found)")

def demo_metrics():
    now = int(time.time())
    timestamps = [now - (SAMPLE_POINTS - i) * 15 for i in range(SAMPLE_POINTS)]
    resp_ms = np.clip(np.random.normal(200, 80, SAMPLE_POINTS).cumsum() / 10 + 100, 20, 5000)
    mem_mb = np.clip(np.random.normal(0.5, 2, SAMPLE_POINTS).cumsum() + 200, 50, 3000)
    err_rate = np.random.choice([0.0, 0.0, 0.0, 0.1, 1.0], SAMPLE_POINTS)
    df = pd.DataFrame({
        "timestamp": timestamps,
        "resp_ms": resp_ms,
        "mem_mb": mem_mb,
        "err_rate": err_rate
    })
    df['time'] = pd.to_datetime(df['timestamp'], unit='s')
    return df

def get_metrics():
    """
    Try to read real DB. If not found or error, return demo dataframe.
    """
    if not os.path.exists(DB_PATH):
        st.info("Database not found — running in demo mode.")
        return demo_metrics()

    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        df = pd.read_sql_query(
            "SELECT timestamp, resp_ms, mem_mb, err_rate FROM metrics ORDER BY id DESC LIMIT 100",
            conn
        )
        conn.close()
        if df.empty:
            st.warning("Database exists but no metrics found. Using demo data.")
            return demo_metrics()
        df['time'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values('time')
        return df
    except Exception as e:
        st.warning(f"Error reading DB — falling back to demo mode. ({e})")
        return demo_metrics()

def get_incidents():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['time','service','type','action','success'])
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        df = pd.read_sql_query(
            "SELECT timestamp, service, type, action, success FROM incidents ORDER BY id DESC LIMIT 10",
            conn
        )
        conn.close()
        if df.empty:
            return df
        df['time'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values('time', ascending=False)
        return df
    except Exception:
        return pd.DataFrame(columns=['time','service','type','action','success'])

# --- Layout ---
metrics_df = get_metrics()
incidents_df = get_incidents()

if metrics_df.empty:
    st.warning("No metrics available at all. Start monitor locally to feed real data.")
else:
    latest_mem = float(metrics_df['mem_mb'].iloc[-1])
    latest_resp = float(metrics_df['resp_ms'].iloc[-1])
    avg_err = float(metrics_df['err_rate'].mean()) * 100

    # status banner
    if latest_mem > 1800 or avg_err > 50 or latest_resp > 2000:
        st.error("CRITICAL: System performance degraded or API unreachable.")
    elif latest_mem > 800 or avg_err > 20 or latest_resp > 1000:
        st.warning("WARNING: Performance degrading; potential issue incoming.")
    else:
        st.success("System stable")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Memory (MB)", f"{latest_mem:.2f}")
        st.metric("Latest Response Time (ms)", f"{latest_resp:.2f}")
    with col2:
        st.metric("Average Error Rate (%)", f"{avg_err:.1f}%")
        st.write("Last updated:", metrics_df['time'].iloc[-1].strftime("%Y-%m-%d %H:%M:%S"))

    st.markdown("### Memory Usage")
    mem_chart = alt.Chart(metrics_df).mark_line().encode(x='time:T', y='mem_mb:Q')
    st.altair_chart(mem_chart, use_container_width=True)

    st.markdown("### Response Time")
    resp_chart = alt.Chart(metrics_df).mark_line().encode(x='time:T', y='resp_ms:Q')
    st.altair_chart(resp_chart, use_container_width=True)

st.markdown("### Healing Actions")
if incidents_df.empty:
    st.info("No healing incidents logged.")
else:
    incidents_df['Status'] = incidents_df['success'].apply(lambda x: "Success" if x == 1 else "Failed")
    st.dataframe(incidents_df[['time','service','type','action','Status']], use_container_width=True)

st.caption("Auto-updates when connected to a live database; otherwise demo data shown.")
