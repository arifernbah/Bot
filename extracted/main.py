
from config.hybrid_loader import HybridConfig

config = HybridConfig()
entry_cfg = config.entry
exit_cfg = config.exit
risk_cfg = config.risk
telegram_cfg = config.telegram

from auto_config_loader import load_config_auto
from bot_modules.bot_runner import BinanceFuturesProBot
from dotenv import load_dotenv
import os
from binance.client import Client

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY") or os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Real-time price fetch ===
def fetch_recent_prices(symbol: str, interval: str, limit: int = 60):
    try:
        api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY", "")
        is_testnet = "testnet" in api_key.lower() if api_key else False
        client = Client(testnet=is_testnet)
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        return [float(kline[4]) for kline in klines]
    except Exception as e:
        print(f"[WARN] Failed to fetch prices: {e}. Returning empty list.")
        return []

if __name__ == "__main__":
    config = load_config_auto()
    bot = BinanceFuturesProBot(
        api_key=API_KEY,
        api_secret=API_SECRET,
        telegram_token=TELEGRAM_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID,
        config=config
    )
    bot.run_forever()
