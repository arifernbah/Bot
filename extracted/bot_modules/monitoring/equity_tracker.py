# 📊 Equity Tracker & Drawdown Monitor
import os
import json
from datetime import datetime

DATA_FILE = "equity_log.json"

def record_equity(value):
    now = datetime.utcnow().isoformat()
    data = {"timestamp": now, "equity": value}
    _save_log(data)

def _save_log(entry):
    logs = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            logs = json.load(f)
    logs.append(entry)
    with open(DATA_FILE, "w") as f:
        json.dump(logs[-100:], f, indent=2)

def get_latest_equity():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r") as f:
        logs = json.load(f)
    return logs[-1] if logs else None
