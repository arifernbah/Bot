"""Detect simple bullish/bearish order blocks (OB)
Defined here as last down candle before strong up move (bullish OB)
 and last up candle before strong down move (bearish OB).
This simplistic implementation counts OB occurrences in lookback.
"""
from typing import List, Dict

__all__ = ["detect_order_blocks"]

def detect_order_blocks(open_: List[float], close: List[float], lookback: int = 30) -> Dict[str, int]:
    bullish = 0
    bearish = 0
    for i in range(2, min(len(close) - 1, lookback)):
        # bullish OB: bearish candle followed by two bullish closes higher than its open
        if close[-i] < open_[-i] and close[-i + 1] > open_[-i] and close[-i + 2] > open_[-i]:
            bullish += 1
        # bearish OB: bullish candle followed by two bearish closes below its open
        if close[-i] > open_[-i] and close[-i + 1] < open_[-i] and close[-i + 2] < open_[-i]:
            bearish += 1
    return {"bullish_ob": bullish, "bearish_ob": bearish}