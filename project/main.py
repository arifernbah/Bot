
from auto_config_loader import load_config_auto
from bot_binance_futures import BinanceFuturesBot
from dotenv import load_dotenv
from kelly_manager import calculate_kelly_fraction
from market_analyzer import detect_market_trend, is_market_safe
import os
# numpy is used in market_analyzer but imported there; no need to import here
from binance.client import Client  # new import

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Real-time price fetch ===
def fetch_recent_prices(symbol: str, interval: str, limit: int = 60):
    """Fetch recent closing prices from Binance Futures public endpoint.

    Args:
        symbol (str): Trading pair symbol, e.g. "BTCUSDT".
        interval (str): Kline interval, e.g. "5m".
        limit (int): Number of klines to retrieve.

    Returns:
        list[float]: List of closing prices.
    """
    try:
        client = Client()  # public endpoints do not require API keys
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        return [float(kline[4]) for kline in klines]
    except Exception as e:
        print(f"[WARN] Failed to fetch prices from Binance: {e}. Falling back to empty list.")
        return []

if __name__ == "__main__":
    config = load_config_auto(API_KEY, API_SECRET)

    # Inject Telegram config
    config['telegram'] = {
        'token': TELEGRAM_TOKEN,
        'chat_id': TELEGRAM_CHAT_ID
    }

    # === Kelly Sizing Activation ===
    if config["initial_balance"] >= 50:
        winrate = 0.75  # example fixed winrate
        tp = config["take_profit"]["tp_percent"]
        sl = config["stop_loss"]["sl_percent"]
        rr = tp / sl
        kelly_fraction = calculate_kelly_fraction(winrate, rr)
        config["position_sizing"]["method"] = "kelly_partial"
        config["position_sizing"]["fraction"] = kelly_fraction
        print(f"[DYNAMIC] Kelly sizing active: {kelly_fraction:.2%}")

    # === Market Safety Check ===
    recent_prices = fetch_recent_prices(config["symbol"], config["timeframe"], 60)
    if not recent_prices:
        print("[WARN] Could not retrieve recent prices; skipping market safety check.")
        safe_to_trade = True
    else:
        trend = detect_market_trend(recent_prices)
        print(f"[DYNAMIC] Market trend: {trend}")
        safe_to_trade = is_market_safe(trend)
    if not safe_to_trade:
        print("[DYNAMIC] Market not safe. Skipping trade execution.")
    else:
        # Initialize and start the async trading bot
        import asyncio

        bot = BinanceFuturesBot()
        try:
            asyncio.run(bot.start())
        except KeyboardInterrupt:
            print("\nBot stopped by user")
