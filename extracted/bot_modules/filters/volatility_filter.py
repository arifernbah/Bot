# 📉 Volatility Filter Module
def is_market_volatile(prices, threshold=0.015):
    """
    Menentukan apakah pasar cukup volatile berdasarkan rentang harga.
    threshold: persentase minimum pergerakan (default 1.5%)
    """
    if not prices or len(prices) < 2:
        return False

    high = max(prices)
    low = min(prices)
    range_pct = (high - low) / low if low != 0 else 0

    return range_pct >= threshold
