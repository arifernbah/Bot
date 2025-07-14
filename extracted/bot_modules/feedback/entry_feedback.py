# 📊 Modul feedback sinyal entry berdasarkan hasil historis

import json
from pathlib import Path

FEEDBACK_FILE = Path("data/feedback_data.json")

def _load_feedback():
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_feedback(data):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, indent=2)

def record_entry_result(strategy_name: str, result: str):
    """
    Catat hasil trade berdasarkan strategi/sinyal yang digunakan.
    result: 'win' atau 'loss'
    """
    data = _load_feedback()
    if strategy_name not in data:
        data[strategy_name] = {"win": 0, "loss": 0}
    data[strategy_name][result] += 1
    _save_feedback(data)

def get_strategy_confidence(strategy_name: str) -> float:
    """
    Hitung confidence score dari strategi berdasarkan rasio win/loss.
    """
    data = _load_feedback()
    stats = data.get(strategy_name, {"win": 0, "loss": 0})
    total = stats["win"] + stats["loss"]
    if total == 0:
        return 1.0  # Default confidence jika belum ada data
    return round(stats["win"] / total, 3)


def should_disable_signal(strategy_name: str, threshold: float = 0.2) -> bool:
    """
    True jika confidence terlalu rendah dan strategi sebaiknya di-nonaktifkan.
    """
    confidence = get_strategy_confidence(strategy_name)
    return confidence < threshold
