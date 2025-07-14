"""Very simple Fair Value Gap (FVG) detector.
Looks for gaps where candle high < previous low (bearish gap) or
candle low > previous high (bullish gap). Returns recent gap count.
"""
from typing import List, Dict

__all__ = ["detect_fvg"]

def detect_fvg(highs: List[float], lows: List[float], lookback: int = 50) -> Dict[str, int]:
    bullish = 0
    bearish = 0
    for i in range(1, min(len(highs), lookback)):
        if lows[-i] > highs[-i - 1]:
            bullish += 1
        elif highs[-i] < lows[-i - 1]:
            bearish += 1
    return {"bullish_fvg": bullish, "bearish_fvg": bearish}