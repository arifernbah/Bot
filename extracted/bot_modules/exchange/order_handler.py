
from bot_modules.monitoring.equity_tracker import get_latest_equity

def determine_order_type(spread_pct: float):
    equity = get_latest_equity() or 0
    if equity >= 50 and spread_pct < 0.2:
        return "LIMIT"
    return "MARKET"


from bot_modules.logging.logger import log

def execute_order(order: dict):
    """
    Simulasikan eksekusi order (MARKET).
    Format order:
    {
        "symbol": "BTCUSDT",
        "side": "SELL" or "BUY",
        "amount": float,
        "type": "MARKET",
        "price": float
    }
    """
    log(f"[ORDER] Executing {order['side']} {order['amount']} {order['symbol']} at MARKET (price={order['price']})")


def place_trailing_order(order: dict):
    """
    Simulasikan trailing stop order.
    Format order:
    {
        "symbol": "BTCUSDT",
        "side": "SELL" or "BUY",
        "amount": float,
        "type": "TRAILING_STOP_MARKET",
        "trail_offset": float,   # in percent
        "trigger_price": float
    }
    """
    log(f"[TRAILING STOP] Placing trailing stop on {order['symbol']} at {order['trigger_price']:.4f} "
        f"with offset {order['trail_offset']}% ({order['side']}, amount={order['amount']})")
