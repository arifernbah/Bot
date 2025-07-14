import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

BINANCE_FUTURES_TICKER_URL = "https://fapi.binance.com/fapi/v1/ticker/24hr"

async def fetch_top_futures_symbols(limit=10, quote="USDT", min_volume=100000000):
    """
    Ambil top symbol dari Binance Futures berdasarkan volume (24h).
    Default: top 10 pair berdenominasi USDT dan volume besar.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BINANCE_FUTURES_TICKER_URL, timeout=10) as resp:
                data = await resp.json()

        filtered = [
            item["symbol"] for item in data
            if item["symbol"].endswith(quote)
            and not item["symbol"].endswith("BULLUSDT")
            and float(item["quoteVolume"]) > min_volume
        ]

        top_symbols = sorted(filtered, key=lambda sym: next(
            float(d["quoteVolume"]) for d in data if d["symbol"] == sym
        ), reverse=True)[:limit]

        logger.info(f"[SYMBOLS] Top {limit} symbols loaded dynamically: {top_symbols}")
        return top_symbols

    except Exception as e:
        logger.warning(f"[SYMBOLS] Failed to load dynamic symbols: {e}")
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # fallback

# Test run
if __name__ == "__main__":
    symbols = asyncio.run(fetch_top_futures_symbols())
    print(symbols)