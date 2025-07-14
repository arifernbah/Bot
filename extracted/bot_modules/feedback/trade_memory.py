# 🧠 Trade memory: simpan hasil terakhir trade tiap symbol

import json
from pathlib import Path
from datetime import datetime, timedelta

MEMORY_FILE = Path("data/trade_memory.json")

def _load_memory():
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def remember_trade_result(symbol: str, result: str):
    """
    Simpan hasil trade terakhir: 'win' atau 'loss'
    """
    data = _load_memory()
    data[symbol] = {
        "result": result,
        "time": datetime.utcnow().isoformat()
    }
    _save_memory(data)

def recent_loss(symbol: str, minutes: int = 60) -> bool:
    data = _load_memory()
    if symbol not in data:
        return False
    entry = data[symbol]
    if entry["result"] != "loss":
        return False
    last_time = datetime.fromisoformat(entry["time"])
    return datetime.utcnow() - last_time < timedelta(minutes=minutes)

def recent_win(symbol: str, minutes: int = 60) -> bool:
    data = _load_memory()
    if symbol not in data:
        return False
    entry = data[symbol]
    if entry["result"] != "win":
        return False
    last_time = datetime.fromisoformat(entry["time"])
    return datetime.utcnow() - last_time < timedelta(minutes=minutes)
