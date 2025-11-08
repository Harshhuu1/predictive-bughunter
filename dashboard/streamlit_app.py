# dashboard/streamlit_app.py
import streamlit as st
import sqlite3
import pandas as pd
import time
import altair as alt

DB = "agents.db"

# --- Page setup ---
st.set_page_config(
    page_title="AI Predictive Bug Hunter Dashboard",
    layout="wide",
    page_icon="🧠"
)

st.title("🧠 AI Predictive Bug Hunter & Auto-Healer Dashboard")
st.caption("Monitoring, predicting, and healing issues before they break production 🚀")

# --- Helper functions ---
def get_metrics():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(
        "SELECT timestamp, resp_ms, mem_mb, err_rate FROM metrics ORDER BY id DESC LIMIT 100",
        conn
    )
    conn.close()
    if not df.empty:
        df['time'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values('time')
    return df

def get_incidents():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(
        "SELECT timestamp, service, type, action, success FROM incidents ORDER BY id DESC LIMIT 10",
        conn
    )
    conn.close()
    if not df.empty:
        df['time'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values('time', ascending=False)
    return df

# --- Live metrics section ---
placeholder = st.empty()

while True:
    with placeholder.container():
        metrics_df = get_metrics()
        incidents_df = get_incidents()

        if metrics_df.empty:
            st.warning("No metrics found yet. Run monitor_agent.py first.")
        else:
            latest_mem = metrics_df['mem_mb'].iloc[-1]
            latest_resp = metrics_df['resp_ms'].iloc[-1]
            avg_err = metrics_df['err_rate'].mean() * 100

            # --- Color-coded alerts ---
            if latest_mem > 1800 or avg_err > 50:
                st.error("🚨 CRITICAL: Memory usage or error rate dangerously high!")
            elif latest_mem > 800 or avg_err > 20:
                st.warning("⚠️ WARNING: System performance degrading, potential issue incoming.")
            else:
                st.success("✅ System stable and healthy.")

            # --- Live metrics ---
            st.subheader("📊 Live Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Memory Usage (MB)", f"{latest_mem:.2f}")
                st.metric("Latest Response Time (ms)", f"{latest_resp:.2f}")
            with col2:
                st.metric("Average Error Rate (%)", f"{avg_err:.1f}%")

            # --- Charts ---
            st.markdown("### 🧠 Memory Usage Trend")
            mem_chart = (
                alt.Chart(metrics_df)
                .mark_line(color="#00BFFF")
                .encode(x="time:T", y="mem_mb:Q")
                .properties(height=250)
            )
            st.altair_chart(mem_chart, use_container_width=True)

            st.markdown("### ⚡ Response Time Trend")
            resp_chart = (
                alt.Chart(metrics_df)
                .mark_line(color="#FFA500")
                .encode(x="time:T", y="resp_ms:Q")
                .properties(height=250)
            )
            st.altair_chart(resp_chart, use_container_width=True)

        # --- Healing actions table ---
        st.subheader("🩹 Healing Actions Log")
        if incidents_df.empty:
            st.info("No incidents logged yet.")
        else:
            incidents_df['Status'] = incidents_df['success'].apply(
                lambda x: "✅ Success" if x == 1 else "❌ Failed"
            )
            st.dataframe(
                incidents_df[['time', 'service', 'type', 'action', 'Status']],
                use_container_width=True,
                hide_index=True
            )

        # --- Refresh info ---
        st.caption("⏱️ Auto-refreshing every 10 seconds...")
    time.sleep(10)
