import asyncio
from collections import defaultdict, deque
from typing import Dict, Deque
from binance import AsyncClient, BinanceSocketManager

class WSPriceCache:
    """Lightweight websocket listener that stores recent klines (close, high, low, open, volume) per symbol.

    Keeps max_len klines in memory (default 100).  Designed for 1-GB VPS: RAM usage ~15 MB for 10 pairs.
    """

    def __init__(self, client: AsyncClient, symbols: list, interval: str = "5m", max_len: int = 100):
        self.client = client
        self.symbols = symbols
        self.interval = interval
        self.max_len = max_len
        self.cache: Dict[str, Deque] = defaultdict(lambda: deque(maxlen=max_len))
        self._task = None

    async def _listener(self):
        mgr = BinanceSocketManager(self.client)
        # Combine-kline stream e.g. btcusdt@kline_5m/ethusdt@kline_5m
        stream_names = [f"{sym.lower()}@kline_{self.interval}" for sym in self.symbols]
        async with mgr._multi_socket(stream_names) as stream:
            async for msg in stream:
                if not msg or msg.get("e") != "kline":
                    continue
                k = msg["k"]
                symbol = msg["s"]
                entry = [
                    k["t"],                    # Open time
                    float(k["o"]),             # Open
                    float(k["h"]),             # High
                    float(k["l"]),             # Low
                    float(k["c"]),             # Close
                    float(k["v"])              # Volume
                ]
                self.cache[symbol].append(entry)

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._listener())

    def get_klines(self, symbol: str, limit: int = 50):
        data = list(self.cache.get(symbol.upper(), []))
        return data[-limit:] if len(data) >= limit else []