# 🎯 Strategy Auto Re-weighting berdasarkan feedback

import json
from pathlib import Path
from bot_modules.feedback.entry_feedback import get_strategy_confidence

WEIGHT_FILE = Path("data/strategy_weights.json")
DEFAULT_WEIGHT = 1.0

def _load_weights():
    if WEIGHT_FILE.exists():
        with open(WEIGHT_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_weights(data):
    with open(WEIGHT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_weight(strategy_name: str) -> float:
    data = _load_weights()
    return data.get(strategy_name, DEFAULT_WEIGHT)

def update_weights_from_feedback():
    # Cek confidence dan ubah bobot strategi
    updated = {}
    strategies = ["rsi_signal", "structure_breakout", "liquidity_surge", "trend_following"]
    for strat in strategies:
        confidence = get_strategy_confidence(strat)
        if confidence >= 0.8:
            weight = 1.2
        elif confidence >= 0.6:
            weight = 1.0
        elif confidence >= 0.4:
            weight = 0.8
        else:
            weight = 0.5
        updated[strat] = round(weight, 2)
    _save_weights(updated)
