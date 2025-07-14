# 📊 Multi-Timeframe Market Context Filter

import numpy as np

def analyze_higher_tf(prices: list, slope_threshold=0.02) -> str:
    """
    Analisis data higher timeframe (misal 1H) untuk arah trend.
    Return: "bullish", "bearish", atau "sideway"
    """
    if len(prices) < 20:
        return "unknown"

    slope = np.polyfit(np.arange(len(prices)), prices, 1)[0]

    if slope > slope_threshold:
        return "bullish"
    elif slope < -slope_threshold:
        return "bearish"
    else:
        return "sideway"
