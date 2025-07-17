import requests
from core.config import config
from utils.logger import logger

def fetch_top_volume_pairs(count=10, quote_asset='USDT'):
    """Ambil top N pairs dengan volume terbesar dari Binance (default USDT)"""
    try:
        url = 'https://api.binance.com/api/v3/ticker/24hr'
        response = requests.get(url, timeout=10)
        data = response.json()
        # Filter hanya pair dengan quote_asset (misal: USDT)
        filtered = [d for d in data if d['symbol'].endswith(quote_asset)]
        # Urutkan berdasarkan volume quoteAsset (misal: quoteVolume USDT)
        sorted_pairs = sorted(filtered, key=lambda x: float(x['quoteVolume']), reverse=True)
        top_pairs = [d['symbol'] for d in sorted_pairs[:count]]
        return top_pairs
    except Exception as e:
        logger.error(f"Gagal fetch top volume pairs: {e}")
        return []

def update_config_trading_pairs():
    """Update config.TRADING_PAIRS jika USE_TOP_VOLUME_PAIRS aktif"""
    if getattr(config, 'USE_TOP_VOLUME_PAIRS', False):
        count = getattr(config, 'TOP_VOLUME_COUNT', 10)
        top_pairs = fetch_top_volume_pairs(count=count)
        if top_pairs:
            config.TRADING_PAIRS = top_pairs
            logger.info(f"TRADING_PAIRS diupdate otomatis: {top_pairs}")
        else:
            logger.warning("Gagal update TRADING_PAIRS, menggunakan default.")