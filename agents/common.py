# agents/common.py
import sqlite3
import time

DB = "agents.db"

def init_db():
    c = sqlite3.connect(DB)
    cur = c.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        service TEXT,
        resp_ms REAL,
        mem_mb REAL,
        err_rate REAL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        service TEXT,
        type TEXT,
        detail TEXT,
        action TEXT,
        success INTEGER
    )""")
    c.commit()
    c.close()

def insert_metric(service: str, resp_ms: float, mem_mb: float, err_rate: float):
    c = sqlite3.connect(DB)
    cur = c.cursor()
    cur.execute("INSERT INTO metrics (timestamp, service, resp_ms, mem_mb, err_rate) VALUES (?, ?, ?, ?, ?)",
                (int(time.time()), service, resp_ms, mem_mb, err_rate))
    c.commit()
    c.close()
