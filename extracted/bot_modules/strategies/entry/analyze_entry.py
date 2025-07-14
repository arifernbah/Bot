"""Smart entry analysis combining basic TA and ICT elements."""
from typing import List, Dict
import numpy as np

from bot_modules.strategies.entry.entry_scoring import calculate_entry_score, is_confident_entry
from bot_modules.ict.liquidity import detect_liquidity_zones
from bot_modules.ict.market_structure import analyze_structure

class SmartEntry:
    """Lightweight yet functional entry analyser used by the bot."""

    def __init__(self, config):
        self.config = config
        self.history: List[Dict] = []  # trade history for learning

    # ------------------------------------------------------------------
    async def analyze_entry(self, klines: List[List]) -> Dict:
        """Return entry decision dict compatible with trade_executor."""
        if len(klines) < 50:
            return {"action": "wait", "confidence": 0, "reason": "insufficient_data"}

        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]

        # Simple RSI (period 14)
        deltas = np.diff(closes)
        seed = deltas[:14]
        up = seed[seed > 0].sum() / 14
        down = -seed[seed < 0].sum() / 14
        rs = up / down if down else 0
        rsi = 100 - 100 / (1 + rs) if down else 100
        rsi_signal = "bullish" if rsi < 35 else "bearish" if rsi > 65 else "neutral"

        # Market structure & liquidity
        structure = analyze_structure(closes)
        liquidity = detect_liquidity_zones(closes)

        structure_sig = "breakout" if structure["bias"] == "bullish" else "breakdown" if structure["bias"] == "bearish" else "ranging"

        signals = {
            "rsi": rsi_signal,
            "structure": structure_sig,
            "sentiment": "bullish" if liquidity["bias"] == "bullish" else "bearish" if liquidity["bias"] == "bearish" else "neutral",
            "is_volatile": np.std(deltas) / np.mean(closes) > 0.005,
        }

        score = calculate_entry_score(signals)
        confidence = min(max(score / 4 * 100, 0), 100)

        action = "wait"
        if is_confident_entry(score):
            action = "long" if structure["bias"] == "bullish" else "short" if structure["bias"] == "bearish" else "wait"

        return {
            "action": action,
            "confidence": confidence,
            "reason": f"score={score}",
            "signals": signals,
        }

    # ------------------------------------------------------------------
    def add_trade_to_history(self, trade_data: Dict):
        self.history.append(trade_data)
        self.history = self.history[-500:]  # keep last 500 trades
