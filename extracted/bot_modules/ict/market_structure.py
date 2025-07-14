"""Simplified market structure analysis.
Returns bullish/bearish/ranging bias based on higher highs/lows over recent swings.
"""
from typing import List, Dict

__all__ = ["analyze_structure"]

def _find_swings(prices: List[float], window: int = 3):
    swings_hi = []
    swings_lo = []
    for i in range(window, len(prices) - window):
        if all(prices[i] > prices[j] for j in range(i - window, i)) and all(prices[i] > prices[j] for j in range(i + 1, i + window + 1)):
            swings_hi.append((i, prices[i]))
        if all(prices[i] < prices[j] for j in range(i - window, i)) and all(prices[i] < prices[j] for j in range(i + 1, i + window + 1)):
            swings_lo.append((i, prices[i]))
    return swings_hi[-2:], swings_lo[-2:]

def analyze_structure(prices: List[float]) -> Dict:
    if len(prices) < 20:
        return {"bias": "neutral", "structure": "insufficient"}
    hi, lo = _find_swings(prices)
    if len(hi) < 2 or len(lo) < 2:
        return {"bias": "neutral", "structure": "insufficient"}
    bias = "neutral"
    if hi[-1][1] > hi[-2][1] and lo[-1][1] > lo[-2][1]:
        bias = "bullish"
    elif hi[-1][1] < hi[-2][1] and lo[-1][1] < lo[-2][1]:
        bias = "bearish"
    return {"bias": bias, "recent_highs": hi, "recent_lows": lo}