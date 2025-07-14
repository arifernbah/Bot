
"""Entry point for running the Binance Futures Pro bot.

This streamlined launcher keeps compatibility with the new `auto_config_loader`
signature *and* the refactored `BinanceFuturesProBot` class that now lives in
`bot_modules.trade_executor`.
"""

import asyncio
import os
from dotenv import load_dotenv

from auto_config_loader import load_config_auto

# Import the bot from its actual module path
from bot_modules.trade_executor import BinanceFuturesProBot


def _load_env() -> tuple[str, str]:
    """Helper to load API credentials from the environment."""
    load_dotenv()
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY", "")
    api_secret = os.getenv("BINANCE_SECRET_KEY") or os.getenv("API_SECRET", "")
    return api_key, api_secret


async def _main() -> None:
    api_key, api_secret = _load_env()

    # Build a dynamic configuration based on live account info
    config = load_config_auto(api_key, api_secret)

    if config is None:
        raise RuntimeError("Failed to load configuration – check API keys.")

    bot = BinanceFuturesProBot(config=config)
    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        print("\n[MAIN] Stopped by user")
    except Exception as exc:
        print(f"[MAIN] Fatal error: {exc}")
