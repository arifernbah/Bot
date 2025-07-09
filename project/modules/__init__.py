"""
Professional Trading Bot Modules - Lightweight & Modular
Optimized untuk VPS 1GB RAM dengan intelligence 10-year pro trader
"""

# Version info
__version__ = "1.0.0"
__author__ = "Pro Trader Bot"

# Core modules for clean imports
from .config_manager import SmartConfig
from .indicators import SmartIndicators
from .market_analysis import MarketRegimeDetector, LiquidityZoneDetector, MarketStructureAnalyzer
from .position_sizing import KellyCriterionCalculator
from .session_timing import TradingSessionAnalyzer
from .smart_trading import SmartEntry, SmartExit
from .telegram_handler import TelegramNotifier
from .ws_feed import WSPriceCache
from .ml_filter import MLFilter

__all__ = [
    "SmartConfig",
    "SmartIndicators", 
    "MarketRegimeDetector",
    "LiquidityZoneDetector",
    "MarketStructureAnalyzer",
    "KellyCriterionCalculator",
    "TradingSessionAnalyzer",
    "SmartEntry",
    "SmartExit",
    "TelegramNotifier"
]
from .position_sizing import VolatilityPositionSizer

try:
    __all__.append('VolatilityPositionSizer')
except Exception:
    pass

# Global constant for total entry+exit fee (e.g., 0.08% on Binance Futures)
FEE_RATE = 0.0008

__all__.extend(["WSPriceCache", "MLFilter"])
