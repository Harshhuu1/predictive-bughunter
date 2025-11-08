# app/main.py
from fastapi import FastAPI
import random, time

app = FastAPI()
start = time.time()

# Simulate a memory leak variable
leak = 0

@app.get("/metrics")
def metrics():
    global leak
    # simulate memory slowly rising
    leak += random.uniform(0, 5)  # MB per call
    resp_ms = random.uniform(50, 150) + (leak*0.3)
    mem_mb = 200 + leak
    err_rate = 0.0 if random.random() > 0.02 else 1.0
    return {"uptime": int(time.time()-start), "resp_ms": resp_ms, "mem_mb": mem_mb, "err_rate": err_rate}
