# 📤 Evaluasi performa strategi EXIT berdasarkan hasil historis

import json
from pathlib import Path

EXIT_LOG_FILE = Path("data/exit_feedback_log.json")

def _load_log():
    if EXIT_LOG_FILE.exists():
        with open(EXIT_LOG_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_log(data):
    with open(EXIT_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_exit_result(trade_id: str, reason: str, result: str):
    """
    Log hasil exit dari suatu trade.
    result: 'win' atau 'loss'
    """
    data = _load_log()
    if reason not in data:
        data[reason] = {"win": 0, "loss": 0}
    data[reason][result] += 1
    _save_log(data)

def analyze_exit_performance(reason: str) -> float:
    """
    Hitung skor performa exit logic tertentu berdasarkan win ratio.
    """
    data = _load_log()
    stats = data.get(reason, {"win": 0, "loss": 0})
    total = stats["win"] + stats["loss"]
    if total == 0:
        return 1.0  # default confidence
    return round(stats["win"] / total, 3)
