"""Compatibility shim.

Re-exports `BinanceFuturesBot` from `core.bot_runner` so existing
scripts that do `import bot_binance_futures` keep working unchanged.
"""
from core.bot_runner import BinanceFuturesBot

__all__ = ["BinanceFuturesBot"]
