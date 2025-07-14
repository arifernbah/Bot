# 📈 Mengukur kekuatan tren berdasarkan slope MA sederhana

import numpy as np

def calculate_trend_strength(prices: list, window: int = 20) -> float:
    """
    Menghitung kekuatan tren dengan slope dari MA (moving average).
    Nilai hasil bisa digunakan sebagai bobot confidence.
    """
    if len(prices) < window:
        return 0.0

    ma = np.convolve(prices, np.ones(window)/window, mode='valid')
    x = np.arange(len(ma))
    # Linear regression (slope)
    slope = np.polyfit(x, ma, 1)[0]
    return round(slope, 5)

def classify_trend_strength(slope: float, threshold: float = 0.02) -> str:
    if slope > threshold:
        return "strong_up"
    elif slope < -threshold:
        return "strong_down"
    else:
        return "weak_or_flat"
