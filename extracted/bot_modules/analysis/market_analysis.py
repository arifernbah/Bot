"""Market analysis utilities providing volatility and trend metrics.
This lightweight implementation keeps CPU/RAM usage low yet supplies
useful analytics for entry / exit logic.

Returned dict example::

    {
        "volatility": 0.032,               # st-dev of returns (last 20)
        "adx": 27.5,
        "plus_di": 28.1,
        "minus_di": 15.4,
        "regime": "trending",             # trending / ranging / volatile
        "market_bias": "bullish",          # bullish / bearish / neutral
        "volume_sma": 1345.2,
        "volume_ratio": 1.73               # current vol / SMA
    }
"""
from __future__ import annotations

from typing import List, Dict, Tuple
import numpy as np

__all__ = ["analyse_market"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    prev_close = np.concatenate(([close[0]], close[:-1]))
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    return tr


def _calculate_adx(high: List[float], low: List[float], close: List[float], period: int = 14) -> Tuple[float, float, float]:
    """Return ADX, +DI, -DI using Wilder’s smoothing."""
    h = np.asarray(high, dtype=float)
    l = np.asarray(low, dtype=float)
    c = np.asarray(close, dtype=float)

    if len(h) <= period + 1:
        return 0.0, 0.0, 0.0

    plus_dm = np.where((h[1:] - h[:-1]) > (l[:-1] - l[1:]), np.maximum(h[1:] - h[:-1], 0), 0)
    minus_dm = np.where((l[:-1] - l[1:]) > (h[1:] - h[:-1]), np.maximum(l[:-1] - l[1:], 0), 0)

    tr = _true_range(h[1:], l[1:], c[1:])

    # Wilder smoothing
    def wilder(arr):
        avg = np.empty_like(arr)
        avg[:period] = np.nan
        avg_val = np.sum(arr[:period])
        avg[period] = avg_val / period
        for i in range(period + 1, len(arr)):
            avg_val = avg_val - (avg_val / period) + arr[i]
            avg[i] = avg_val / period
        return avg

    sm_plus_dm = wilder(plus_dm)
    sm_minus_dm = wilder(minus_dm)
    sm_tr = wilder(tr)

    plus_di = 100 * sm_plus_dm / sm_tr
    minus_di = 100 * sm_minus_dm / sm_tr
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_series = wilder(dx)

    adx = float(adx_series[-1]) if not np.isnan(adx_series[-1]) else 0.0
    pdi = float(plus_di[-1]) if not np.isnan(plus_di[-1]) else 0.0
    mdi = float(minus_di[-1]) if not np.isnan(minus_di[-1]) else 0.0
    return adx, pdi, mdi


def _classify_regime(adx: float, volatility: float) -> str:
    """Return "trending" / "ranging" / "volatile" based on thresholds."""
    if adx > 25 and volatility < 0.05:
        return "trending"
    if volatility > 0.07:
        return "volatile"
    return "ranging"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_market(klines: List[List]) -> Dict[str, float]:
    """Analyse OHLCV list (as returned by Binance) and return metrics."""
    if len(klines) < 20:
        return {
            "volatility": 0.0,
            "adx": 0.0,
            "plus_di": 0.0,
            "minus_di": 0.0,
            "regime": "neutral",
            "market_bias": "neutral",
            "volume_sma": 0.0,
            "volume_ratio": 0.0,
        }

    high = [float(k[2]) for k in klines]
    low = [float(k[3]) for k in klines]
    close = [float(k[4]) for k in klines]
    volume = [float(k[5]) for k in klines]

    # Volatility – standard deviation of log returns (last 20 bars)
    returns = np.diff(np.log(close))
    volatility = float(np.std(returns[-20:])) if len(returns) >= 20 else float(np.std(returns))

    # Trend metrics
    adx, plus_di, minus_di = _calculate_adx(high, low, close)

    regime = _classify_regime(adx, volatility)

    # Volume analysis
    volume_arr = np.asarray(volume, dtype=float)
    volume_sma = float(np.mean(volume_arr[-20:])) if len(volume_arr) >= 20 else float(np.mean(volume_arr))
    current_vol = volume_arr[-1]
    volume_ratio = float(current_vol / volume_sma) if volume_sma else 0.0

    market_bias = "bullish" if plus_di > minus_di else "bearish" if minus_di > plus_di else "neutral"

    return {
        "volatility": volatility,
        "adx": adx,
        "plus_di": plus_di,
        "minus_di": minus_di,
        "regime": regime,
        "market_bias": market_bias,
        "volume_sma": volume_sma,
        "volume_ratio": volume_ratio,
    }