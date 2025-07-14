# 📊 Deteksi konteks pasar: trending, ranging, volatile

import numpy as np

def detect_market_context(prices: list, window: int = 20) -> str:
    """
    Deteksi apakah market sedang trending, ranging, atau volatile.
    """
    if len(prices) < window:
        return "unknown"

    recent = prices[-window:]
    mean = np.mean(recent)
    std = np.std(recent)
    slope = np.polyfit(np.arange(window), recent, 1)[0]

    # Threshold bisa disesuaikan
    slope_threshold = 0.02
    std_threshold = 0.01 * mean

    if abs(slope) > slope_threshold and std < std_threshold:
        return "trend"
    elif std > std_threshold and abs(slope) < slope_threshold:
        return "range"
    elif std > std_threshold and abs(slope) > slope_threshold:
        return "volatile"
    else:
        return "calm"
