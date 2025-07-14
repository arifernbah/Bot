from telegram.ext import Application
import os

def init_telegram_app() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN tidak ditemukan di environment.")
    return Application.builder().token(token).build()
