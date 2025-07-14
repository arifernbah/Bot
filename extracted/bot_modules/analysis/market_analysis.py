"""Minimal market analysis stub to satisfy imports during runtime.
A real implementation would include complex market regime detection.
"""

def analyse_market(*_, **__):  # noqa: D401
    return {
        "market_bias": "neutral",
        "volatility": 0.03,
    }