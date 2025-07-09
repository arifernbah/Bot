
from auto_config_loader import load_config_auto
from bot import Bot
from dotenv import load_dotenv
from kelly_manager import calculate_kelly_fraction
from market_analyzer import detect_market_trend, is_market_safe
import os
import numpy as np

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_dummy_prices():
    # Replace with real price feed from exchange in real implementation
    return [59000 + np.sin(i/5)*100 for i in range(60)]

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
    recent_prices = get_dummy_prices()
    trend = detect_market_trend(recent_prices)
    print(f"[DYNAMIC] Market trend: {trend}")
    if not is_market_safe(trend):
        print("[DYNAMIC] Market not safe. Skipping trade execution.")
    else:
        bot = Bot(config)
        bot.run()
