
from binance.client import Client
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def fetch_ohlcv(symbol="BTCUSDT", interval="15m", limit=1000):
    client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)

    data = []
    for k in klines:
        data.append({
            "timestamp": datetime.fromtimestamp(k[0] / 1000),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5])
        })
    return data
