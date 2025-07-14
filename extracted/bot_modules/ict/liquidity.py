"""Basic liquidity zone detector (ICT-inspired).
This is intentionally simplified to keep computational load low.
It identifies relative equal highs / lows and recent swing liquidity.
"""
from typing import List, Dict
import numpy as np

__all__ = ["detect_liquidity_zones"]

def detect_liquidity_zones(prices: List[float], lookback: int = 100) -> Dict:
    if len(prices) < lookback:
        lookback = len(prices)
    recent = prices[-lookback:]
    highs = np.array(recent)
    lows = np.array(recent)
    # Simple measure – use top 3 highs & lows
    top = float(np.max(highs))
    bottom = float(np.min(lows))
    eq_highs = [p for p in recent if abs(p - top) / top < 0.002]  # within 0.2 %
    eq_lows = [p for p in recent if abs(p - bottom) / bottom < 0.002]
    bias = "bullish" if prices[-1] > (top + bottom) / 2 else "bearish"
    return {
        "daily_high": top,
        "daily_low": bottom,
        "equal_high_count": len(eq_highs),
        "equal_low_count": len(eq_lows),
        "bias": bias,
    }