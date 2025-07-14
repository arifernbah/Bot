
import traceback
from bot_modules.logging.logger import setup_logger

logger = setup_logger("bot")

def safe_run(func, *args, retries=0, on_fail=None, **kwargs):
    attempt = 0
    while attempt <= retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"[ERROR] ({func.__name__}) failed on attempt {attempt + 1}: {e}")
            traceback.print_exc()
            attempt += 1
    logger.error(f"❌ {func.__name__} failed after {retries+1} attempts.")
    if on_fail:
        on_fail()
    return None

def order_retry(order_func, retries=3):
    for i in range(retries):
        try:
            return order_func()
        except Exception as e:
            logger.warning(f"[RETRY] Order failed (attempt {i+1}): {e}")
    logger.error("❌ Order permanently failed after retries.")
    return None

def notify_telegram(message):
    import requests
    token = "YOUR_TELEGRAM_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message})
    except Exception as e:
        logger.warning(f"⚠️ Failed to send Telegram alert: {e}")
