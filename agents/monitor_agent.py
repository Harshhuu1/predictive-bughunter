import sys
import asyncio
import aiohttp
import time
from agents.common import init_db, insert_metric

# --- Configuration ---
SERVICE_NAME = "real-service"
TARGET_URL = "https://api.github.com"  # Replace with any real API you want to track
POLL_INTERVAL = 30  # seconds

# --- Fix for Windows print buffering ---
sys.stdout.reconfigure(line_buffering=True)

# --- Monitor single API request ---
async def poll_once(session):
    start = time.time()
    try:
        async with session.get(TARGET_URL, timeout=10) as response:
            resp_time = (time.time() - start) * 1000  # convert to ms
            status = response.status
            err_rate = 0.0 if status == 200 else 1.0
            mem_mb = 0.0  # for public APIs, memory usage not tracked

            insert_metric(SERVICE_NAME, resp_time, mem_mb, err_rate)
            print(f"[Monitor] Status={status}, Time={resp_time:.2f}ms, Error={err_rate}")

    except aiohttp.ClientError as e:
        # Network-level error (timeout, DNS, etc.)
        insert_metric(SERVICE_NAME, 9999.0, 0.0, 1.0)
        print(f"[Monitor] Network error: {e}")
    except Exception as e:
        # Catch-all for unexpected errors
        insert_metric(SERVICE_NAME, 9999.0, 0.0, 1.0)
        print(f"[Monitor] Unexpected error: {e}")

# --- Main loop ---
async def run_monitor():
    init_db()
    print(f"[Monitor] Started monitoring {TARGET_URL} every {POLL_INTERVAL}s...")
    async with aiohttp.ClientSession() as session:
        while True:
            await poll_once(session)
            await asyncio.sleep(POLL_INTERVAL)

# --- Entry point ---
if __name__ == "__main__":
    try:
        asyncio.run(run_monitor())
    except KeyboardInterrupt:
        print("\n[Monitor] Stopped manually by user.")
