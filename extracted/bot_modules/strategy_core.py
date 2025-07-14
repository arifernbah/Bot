from bot_modules.exchange.order_handler import execute_order, place_trailing_order, determine_order_type
from bot_modules.logging.logger import setup_logger
logger = setup_logger('bot')

from config.hybrid_loader import HybridConfig
import importlib

config = HybridConfig()
logger.info('Config loaded successfully')
entry_cfg = config.entry
exit_cfg = config.exit
risk_cfg = config.risk
telegram_cfg = config.telegram

def load_entry_strategy(name):
    try:
        module = importlib.import_module(f"bot_modules.strategies.entry.{name}_entry")
        return module
    except ModuleNotFoundError:
        logger.error(f"Entry strategy '{name}' not found.")
        raise

def load_exit_strategy(name):
    try:
        module = importlib.import_module(f"bot_modules.strategies.exit.{name}_exit")
        return module
    except ModuleNotFoundError:
        logger.error(f"Exit strategy '{name}' not found.")
        raise

# Load the strategy modules dynamically
entry_strategy = load_entry_strategy(entry_cfg["name"])
exit_strategy = load_exit_strategy(exit_cfg["name"])

def should_enter(symbol_data, **kwargs):
    return entry_strategy.should_enter(symbol_data, **kwargs)

def should_exit(symbol_data, **kwargs):
    return exit_strategy.should_exit(symbol_data, **kwargs)

# ⬇️ [AUTO-HOOKED] Tambahan integrasi modul baru
from bot_modules.filters.volatility_filter import is_market_volatile
from bot_modules.monitoring.equity_tracker import record_equity
from bot_modules.sentiment.news_sentiment import fetch_sentiment

def pre_trade_checks(price_data, account_equity):
    sentiment = fetch_sentiment()
    is_volatile = is_market_volatile(price_data)
    record_equity(account_equity)

    print(f"[PRE-CHECK] Sentiment: {sentiment}, Volatile: {is_volatile}, Equity: {account_equity}")
    return sentiment, is_volatile
# ⬆️ [AUTO-HOOKED]


def choose_best_exit_strategy():
    # Evaluasi skor performa masing-masing exit
    exits = {
        "volatility_exit": analyze_exit_performance("volatility_exit"),
        "momentum_exit": analyze_exit_performance("momentum_exit"),
        "structure_exit": analyze_exit_performance("structure_exit")
    }
    # Pilih yang terbaik
    best = max(exits.items(), key=lambda x: x[1])
    return best[0]


def execute_partial_exit(position, percent=0.5):
    size_to_close = position["size"] * percent
    symbol = position["symbol"]
    current_price = position.get("current_price", None)
    spread_pct = position.get("spread_pct", 0.5)  # fallback default
    order_type = determine_order_type(spread_pct)

    if current_price is None:
        log(f"[ERROR] Cannot partial exit: no current price for {symbol}")
        return

    order = {
        "symbol": symbol,
        "side": "SELL" if position["side"] == "LONG" else "BUY",
        "amount": size_to_close,
        "type": "MARKET",
        "price": current_price
    }

    log(f"[Partial Exit] Sending market order to close {size_to_close} of {symbol} at market price.")
    execute_order(order)  # You must implement this in your exchange handler

def place_trailing_stop(position, offset_pct=2.0):
    # 🚀 TODO: Replace with real trailing stop logic
    price = position["entry_price"]
    trail_price = price * (1 + offset_pct / 100)
    log(f"[Trailing Stop] Activated at {trail_price:.2f} for {position['symbol']}")
