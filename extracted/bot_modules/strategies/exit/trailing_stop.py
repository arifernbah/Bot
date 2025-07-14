"""Fee-aware trailing stop helper.
Returns dict {should_exit: bool, reason: str}
"""
from typing import List, Dict
from bot_modules.core.constants import get_fee_rate

__all__ = ["trailing_stop"]

def trailing_stop(
    entry_price: float,
    closes: List[float],
    high_prices: List[float],
    low_prices: List[float],
    side: str,
    profit_pct: float,
    mode: str = "profit",
    fee_buffer: float | None = None,
    trail_pct: float = 0.2,
) -> Dict:
    """Simple trailing-stop that respects fee.
    fee_buffer – if None will use 2× taker fee (entry+exit).
    trail_pct    – % distance (e.g. 0.2 = 0.2 %)
    """
    if fee_buffer is None:
        fee_buffer = get_fee_rate() * 2  # entry + exit cost

    if not closes:
        return {"should_exit": False}

    last_close = closes[-1]

    if side == "long":
        peak = max(high_prices) if high_prices else last_close
        trigger = peak * (1 - (trail_pct + fee_buffer))
        if last_close <= trigger:
            return {"should_exit": True, "reason": "trailing_hit"}
    else:  # short
        trough = min(low_prices) if low_prices else last_close
        trigger = trough * (1 + (trail_pct + fee_buffer))
        if last_close >= trigger:
            return {"should_exit": True, "reason": "trailing_hit"}

    return {"should_exit": False}