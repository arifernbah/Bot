from telegram.ext import CommandHandler
from core.telegram import handler

def register_telegram_handlers(app):
    app.add_handler(CommandHandler("start", handler.telegram_start))
    app.add_handler(CommandHandler("status", handler.telegram_status))
    app.add_handler(CommandHandler("balance", handler.telegram_balance))
    app.add_handler(CommandHandler("performance", handler.telegram_performance))
    app.add_handler(CommandHandler("mode", handler.telegram_mode))
    app.add_handler(CommandHandler("testnet", handler.telegram_testnet))
    app.add_handler(CommandHandler("real", handler.telegram_real))
    app.add_handler(CommandHandler("stop", handler.telegram_stop))
    app.add_handler(CommandHandler("help", handler.telegram_help))
    app.add_handler(CommandHandler("upgrade", handler.telegram_upgrade))
    app.add_handler(CommandHandler("equity", handler.telegram_equity))
    app.add_handler(CommandHandler("risk", handler.telegram_risk))
    app.add_handler(CommandHandler("topvolume", handler.telegram_topvolume))
    app.add_handler(CommandHandler("risklevel", handler.telegram_set_risklevel))
    app.add_handler(CommandHandler("maxop", handler.telegram_set_maxop))
