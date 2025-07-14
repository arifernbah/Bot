"""Smart entry analysis combining basic TA and ICT elements."""
from typing import List, Dict
import numpy as np

from bot_modules.strategies.entry.entry_scoring import calculate_entry_score, is_confident_entry
from bot_modules.ict.liquidity import detect_liquidity_zones
from bot_modules.ict.market_structure import analyze_structure
from bot_modules.ict.order_blocks import detect_order_blocks
from bot_modules.ict.fvg import detect_fvg
from bot_modules.risk.position_sizing import KellyCriterionCalculator

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
        opens = [float(k[1]) for k in klines]

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
        ob = detect_order_blocks(opens, closes)
        fvg = detect_fvg(highs, lows)

        structure_sig = "breakout" if structure["bias"] == "bullish" else "breakdown" if structure["bias"] == "bearish" else "ranging"

        signals = {
            "rsi": rsi_signal,
            "structure": structure_sig,
            "sentiment": "bullish" if liquidity["bias"] == "bullish" else "bearish" if liquidity["bias"] == "bearish" else "neutral",
            "is_volatile": np.std(deltas) / np.mean(closes) > 0.005,
            "bullish_ob": ob["bullish_ob"],
            "bearish_ob": ob["bearish_ob"],
            "bullish_fvg": fvg["bullish_fvg"],
            "bearish_fvg": fvg["bearish_fvg"],
        }

        # Extra score contributions from order blocks / FVG
        extra = 1 if (side := structure["bias"]) == "bullish" and ob["bullish_ob"] else 0
        extra += 1 if side == "bearish" and ob["bearish_ob"] else 0
        extra += 1 if side == "bullish" and fvg["bullish_fvg"] else 0
        extra += 1 if side == "bearish" and fvg["bearish_fvg"] else 0

        score = calculate_entry_score(signals) + extra
        confidence = min(max(score / 4 * 100, 0), 100)

        action = "wait"
        if is_confident_entry(score):
            action = "long" if structure["bias"] == "bullish" else "short" if structure["bias"] == "bearish" else "wait"

        return {
            "action": action,
            "confidence": confidence,
            "reason": f"score={score}",
            "signals": signals,
            "position_sizing": self._compute_position_sizing(confidence, symbol=self.config.get("symbol", "BTCUSDT"), balance=self.config.get("initial_balance", 100)),
        }

    # ------------------------------------------------------------------
    def add_trade_to_history(self, trade_data: Dict):
        self.history.append(trade_data)
        self.history = self.history[-500:]  # keep last 500 trades

    # ------------------------------------------------------------------
    def _compute_position_sizing(self, confidence: float, symbol: str, balance: float) -> Dict:
        kelly_pct = 0.0
        if hasattr(self.config, "equity_trader"):
            kelly_pct = getattr(self.config.equity_trader, "kelly_multiplier", 0.0)
        calc = KellyCriterionCalculator()
        return calc.calculate_position_size(symbol, balance, kelly_pct, confidence)
