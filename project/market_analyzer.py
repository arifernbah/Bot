
import numpy as np

def detect_market_trend(prices):
    ema_short = np.mean(prices[-20:])
    ema_long = np.mean(prices[-50:])
    if ema_short > ema_long:
        return "uptrend"
    elif ema_short < ema_long:
        return "downtrend"
    return "sideways"

def is_market_safe(trend):
    return trend in ["sideways", "uptrend"]
