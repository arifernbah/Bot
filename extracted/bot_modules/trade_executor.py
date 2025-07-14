from bot_modules.exchange.order_handler import determine_order_type
#!/usr/bin/env python3
"""
Bot Trading Binance Futures - MODULAR PRO TRADER EDITION
Struktur modular yang ringan dengan intelligence professional
"""

import asyncio
import logging
import logging.handlers
from bot_modules.core.constants import get_fee_rate
import time
from datetime import datetime
from typing import Dict, Any, Optional
import gc
import psutil
import os
import subprocess
import numpy as np

# Binance imports
from binance import AsyncClient, BinanceSocketManager
from binance.enums import *
from binance.exceptions import BinanceAPIException

# Telegram imports
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import threading

# Replace the missing 'modules' package with direct imports. Some of the advanced
# analytical classes are not yet implemented in the public repo – to keep the
# bot runnable we provide ultra-light fallback shims.

from bot_modules.config.config_manager import SmartConfig
from bot_modules.risk.position_sizing import KellyCriterionCalculator
from bot_modules.monitoring.performance_monitor import PerformanceMonitor
from bot_modules.shared.attrdict import AttrDict

# Graceful fallbacks for optional pro-grade modules

class _MissingStub:
    """Minimal stub class used when optional modules are unavailable."""
    def __init__(self, *_, **__):
        pass
    def __getattr__(self, item):
        return _MissingStub()
    def __call__(self, *_, **__):
        return None

try:
    from bot_modules.strategies.entry.analyze_entry import evaluate_entry_signals as _dummy
    from bot_modules.strategies.entry.entry_scoring import calculate_entry_score  # noqa: F401
    # If import succeeds, assume SmartEntry / SmartExit are implemented elsewhere
    from bot_modules.strategies.entry.analyze_entry import SmartEntry  # type: ignore
    from bot_modules.strategies.exit.should_exit import SmartExit  # type: ignore
except Exception:  # pragma: no cover – optional modules missing
    SmartEntry = _MissingStub  # type: ignore
    SmartExit = _MissingStub   # type: ignore

# Optional analysis helpers – ignore if missing
try:
    from bot_modules.analysis.market_analysis import MarketRegimeDetector, MarketStructureAnalyzer
    from bot_modules.analysis.market_context import LiquidityZoneDetector
    from bot_modules.analysis.sentiment import SmartIndicators  # hypothetical
    from bot_modules.utils.session_timing import TradingSessionAnalyzer
except Exception:  # pragma: no cover
    MarketRegimeDetector = _MissingStub  # type: ignore
    MarketStructureAnalyzer = _MissingStub  # type: ignore
    LiquidityZoneDetector = _MissingStub  # type: ignore
    SmartIndicators = _MissingStub  # type: ignore
    TradingSessionAnalyzer = _MissingStub  # type: ignore

# Telegram notifier – fallback to simple print if not available
try:
    from bot_modules.telegram.telegram.handler import TelegramNotifier  # typing: ignore
except Exception:
    class TelegramNotifier:  # type: ignore
        def __init__(self, *_, **__):
            pass
        async def send_casual_message(self, msg: str):
            print(f"[TG] {msg}")
        def get_entry_message(self, *args, **kwargs):
            return "Entry executed"
        def get_exit_message(self, *args, **kwargs):
            return "Exit executed"
        def get_startup_message(self):
            return "Bot started"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler('bot.log', maxBytes=1024*1024, backupCount=1),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Minimum equity to allow trading (USDT)
MIN_BALANCE = 5.0

class BinanceFuturesProBot:
    """
    Professional Trading Bot dengan Modular Structure
    - Intelligence: 10-year Professional Trader
    - Architecture: Hedge Fund Grade  
    - Memory: Optimized untuk VPS 1GB
    - Style: Casual Indonesian dengan data Professional
    """
    
    def __init__(self, config=None):
        # Initialize configuration with equity support
        if config:
            # Accept both SmartConfig objects and plain dictionaries.
            # If the caller supplies a dict (e.g. from auto_config_loader), wrap
            # it in `AttrDict` so the rest of the bot can use attribute access
            # transparently (self.config.is_testnet, self.config.api_key, …).
            if isinstance(config, dict):
                self.config = AttrDict(config)
            else:
                self.config = config
        else:
            self.config = SmartConfig()
            
        # Support multiple symbols
        self.symbols = self.config.get('symbols', [self.config.get('symbol', 'BTCUSDT')])
        # For backward compatibility
        if not hasattr(self.config, 'symbols') and not isinstance(self.config, dict):
            self.symbols = [self.config.symbol]

        # Initialize Binance client
        self.client: Optional[AsyncClient] = None
        
        # Initialize enhanced equity trader if available
        self.equity_trader = self.config.get('equity_trader') if isinstance(self.config, dict) else None
        if self.equity_trader:
            logger.info(f"[EQUITY] Enhanced equity system loaded")
            logger.info(f"[EQUITY] Risk Level: {self.equity_trader.risk_level}")
            logger.info(f"[EQUITY] Base Risk: {self.equity_trader.base_risk_percent}%")
        
        # Initialize professional modules (MODULAR!)
        self.smart_entry = SmartEntry(self.config)
        self.smart_exit = SmartExit(self.config)
        
        # Handle telegram config
        if isinstance(self.config, dict):
            telegram_config = self.config.get('telegram', {})
            telegram_token = telegram_config.get('token') or self.config.get('telegram_token')
            telegram_chat_id = telegram_config.get('chat_id') or self.config.get('telegram_chat_id')
        else:
            telegram_token = getattr(self.config, 'telegram_token', None)
            telegram_chat_id = getattr(self.config, 'telegram_chat_id', None)
        
        self.telegram = TelegramNotifier(telegram_token, telegram_chat_id)
        self.position_sizing = KellyCriterionCalculator()
        
        # Bot state
        self.is_running = False
        self.positions = {}
        self.last_price_data = {}
        self.memory_optimization_counter = 0
        self.active_entries = {}  # Track entry analysis for pro exits
        
        # Initialize performance monitor
        self.performance_monitor = PerformanceMonitor()
        
        # Performance monitoring
        self.process = psutil.Process()
        self.telegram_app = None
        
    async def get_top_volume_symbols(self, limit=10):
        """Get top 10 volume symbols from Binance Futures"""
        try:
            # Get 24h ticker statistics
            tickers = await self.client.futures_ticker()
            
            # Filter USDT pairs and sort by volume
            usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
            sorted_by_volume = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
            
            # Get top 10
            top_symbols = sorted_by_volume[:limit]
            
            logger.info(f"Top {limit} volume symbols: {[s['symbol'] for s in top_symbols]}")
            return top_symbols
            
        except Exception as e:
            logger.error(f"Error getting top volume symbols: {e}")
            return []

    async def get_tradeable_symbols(self, balance):
        """Get list of symbols from top volume that can be traded with current balance"""
        try:
            top_symbols = await self.get_top_volume_symbols(10)
            tradeable_symbols = []
            
            # Get exchange info for minimum quantities
            exchange_info = await self.client.futures_exchange_info()
            
            for symbol_data in top_symbols:
                symbol = symbol_data['symbol']
                
                # Get symbol info
                symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
                if not symbol_info:
                    continue
                
                # Get minimum quantity
                lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                if not lot_size_filter:
                    continue
                
                min_qty = float(lot_size_filter['minQty'])
                
                # Get current price
                ticker = await self.client.futures_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])

                # Hitung spread_pct sederhana dari best bid/ask (default fallback)
                depth = await self.client.futures_order_book(symbol=symbol)
                bid = float(depth['bids'][0][0])
                ask = float(depth['asks'][0][0])
                mid = (bid + ask) / 2
                spread_pct = abs(ask - bid) / mid * 100
                order_type = determine_order_type(spread_pct)
                logger.info(f"[ORDER] Using order type: {order_type} (spread={spread_pct:.4f}%)")

                # Calculate minimum order value
                min_order_value = min_qty * current_price

                # Check if balance is enough (with 5x leverage)
                leverage = 5
                min_balance_needed = min_order_value / leverage

                logger.info(
                    f"Symbol: {symbol}, Min Order Value: ${min_order_value:.4f}, Min Balance Needed: ${min_balance_needed:.2f}"
                )

                if balance >= min_balance_needed:
                    tradeable_symbols.append(symbol)
                    logger.info(f"✅ {symbol} tradeable with balance ${balance:.2f}")
                else:
                    logger.info(
                        f"❌ {symbol} requires ${min_balance_needed:.2f}, balance ${balance:.2f} insufficient"
                    )
            
            logger.info(f"Tradeable symbols: {tradeable_symbols}")
            return tradeable_symbols
            
        except Exception as e:
            logger.error(f"Error getting tradeable symbols: {e}")
            return []

    async def init_binance_client(self) -> bool:
        """Initialize Binance client dengan error handling"""
        try:
            if self.config.is_testnet:
                await self.telegram.send_casual_message("🧪 *Mode TESTNET*\nSantai aja, ini cuma latihan!")
            else:
                await self.telegram.send_casual_message("🚨 *MODE REAL TRADING*\nHati-hati ya, ini duit beneran!")
            
            if not self.config.api_key or not self.config.api_secret:
                logger.error("API keys tidak tersedia")
                return False
            
            self.client = await AsyncClient.create(
                api_key=self.config.api_key,
                api_secret=self.config.api_secret,
                testnet=self.config.is_testnet
            )
            
            # Test connection dengan Futures API
            try:
                # Gunakan futures_account_balance() yang lebih reliable
                balances = await self.client.futures_account_balance()
                usdt_balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
                
                logger.info(f"Connected to Binance Futures. Balance: {usdt_balance} USDT")
                await self.telegram.send_casual_message(f"✅ *Konek ke Binance Futures berhasil!*\nSaldo: ${usdt_balance:.2f}")
                
                # Hard stop if equity below 5 USDT
                if usdt_balance < MIN_BALANCE:
                    await self.telegram.send_casual_message("⚠️ Equity < $5 – Trading halted until balance >= $5")
                    return False

                # Get tradeable symbols from top volume
                tradeable_symbols = await self.get_tradeable_symbols(usdt_balance)
                if tradeable_symbols:
                    self.symbols = tradeable_symbols  # Monitor all tradeable symbols
                    logger.info(f"Monitoring {len(tradeable_symbols)} symbols: {tradeable_symbols}")
                    await self.telegram.send_casual_message(f"🎯 *Monitoring {len(tradeable_symbols)} symbols:*\n{', '.join(tradeable_symbols)}")
                else:
                    await self.telegram.send_casual_message(f"⚠️ *Balance ${usdt_balance:.2f} tidak cukup untuk trading*\nBot akan skip trading sampai balance cukup")
                    return False
                
                return True
            except Exception as e:
                logger.error(f"Error testing Futures connection: {e}")
                await self.telegram.send_casual_message(f"❌ Gagal test koneksi Futures: {str(e)}")
                return False
        except BinanceAPIException as e:
            logger.error(f"Binance API Error: {e}")
            await self.telegram.send_casual_message(f"❌ Binance API Error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error initializing Binance client: {e}")
            await self.telegram.send_casual_message(f"❌ Error koneksi Binance: {str(e)}")
            return False
    
    async def init_telegram_bot(self):
        """Initialize Telegram bot dengan commands (simple approach)"""
        try:
            if not self.config.telegram_token:
                logger.warning("Telegram token tidak tersedia")
                return
            
            self.telegram_app = Application.builder().token(self.config.telegram_token).build()
            
            # Command handlers
            self.telegram_app.add_handler(CommandHandler("start", self.telegram_start))
            self.telegram_app.add_handler(CommandHandler("status", self.telegram_status))
            self.telegram_app.add_handler(CommandHandler("balance", self.telegram_balance))
            self.telegram_app.add_handler(CommandHandler("performance", self.telegram_performance))
            self.telegram_app.add_handler(CommandHandler("mode", self.telegram_mode))
            self.telegram_app.add_handler(CommandHandler("testnet", self.telegram_testnet))
            self.telegram_app.add_handler(CommandHandler("real", self.telegram_real))
            self.telegram_app.add_handler(CommandHandler("stop", self.telegram_stop))
            self.telegram_app.add_handler(CommandHandler("help", self.telegram_help))
            self.telegram_app.add_handler(CommandHandler("upgrade", self.telegram_upgrade))
            self.telegram_app.add_handler(CommandHandler("equity", self.telegram_equity))
            self.telegram_app.add_handler(CommandHandler("risk", self.telegram_risk))
            # New: refresh symbols to top-volume
            self.telegram_app.add_handler(CommandHandler("topvolume", self.telegram_topvolume))
            # New: set risk level & max open positions
            self.telegram_app.add_handler(CommandHandler("risklevel", self.telegram_set_risklevel))
            self.telegram_app.add_handler(CommandHandler("maxop", self.telegram_set_maxop))
            
            # Handle unknown commands
            self.telegram_app.add_handler(MessageHandler(filters.COMMAND, self.telegram_unknown_command))
            
            logger.info("Telegram bot initialized with professional commands")
            
            # Initialize but don't start polling yet
            await self.telegram_app.initialize()
            
            # Wait a bit for initialization to complete
            await asyncio.sleep(2)
            
            # Register commands with Telegram to show in menu
            await self.register_telegram_commands()
            
            # Wait a bit more for commands to be registered
            await asyncio.sleep(1)
            
            logger.info("Telegram bot ready for polling")
            
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")

    async def register_telegram_commands(self):
        """Register commands with Telegram so they appear in the command menu"""
        try:
            commands = [
                ("start", "🚀 Start bot dan welcome message"),
                ("help", "📖 Daftar semua command yang tersedia"), 
                ("status", "📊 Status bot dan kondisi trading"),
                ("balance", "💰 Cek saldo dan pertumbuhan"),
                ("performance", "📈 Rekap performa trading"),
                ("equity", "⚖️ Info equity trading dan DD"),
                ("risk", "⚠️ Analisa risk management"),
                ("mode", "🔄 Cek mode trading (real/test)"),
                ("testnet", "🧪 Switch ke testnet mode"),
                ("real", "💎 Switch ke real trading"),
                ("topvolume", "📊 Update ke 10 pair volume tertinggi"),
                ("risklevel", "⚖️ Set risk level trading"),
                ("maxop", "🎯 Set max open positions"),
                ("stop", "🛑 Stop bot dengan aman")
            ]
            
            logger.info(f"📝 Registering {len(commands)} Telegram commands...")
            
            # Try to register commands
            result = await self.telegram_app.bot.set_my_commands(commands)
            logger.info(f"✅ Telegram commands registered successfully: {result}")
            
            # Verify commands were set
            try:
                current_commands = await self.telegram_app.bot.get_my_commands()
                logger.info(f"📋 Current commands: {len(current_commands)} commands found")
                for cmd in current_commands:
                    logger.info(f"  - /{cmd.command}: {cmd.description}")
            except Exception as e:
                logger.error(f"❌ Error verifying commands: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error registering Telegram commands: {e}")
            # Try alternative method
            try:
                logger.info("🔄 Trying alternative command registration...")
                for command, description in commands:
                    await self.telegram_app.bot.set_my_commands([(command, description)])
                logger.info("✅ Alternative command registration successful")
            except Exception as e2:
                logger.error(f"❌ Alternative registration also failed: {e2}")

    async def start_telegram_polling(self):
        """Start Telegram polling as separate task"""
        try:
            if self.telegram_app:
                logger.info("Starting Telegram polling...")
                # Use start_polling instead of run_polling to avoid blocking
                await self.telegram_app.start()
                await self.telegram_app.updater.start_polling()
                logger.info("Telegram polling started successfully")
                
                # Keep the polling running
                while self.is_running:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error starting Telegram polling: {e}")
        finally:
            if self.telegram_app:
                try:
                    await self.telegram_app.updater.stop()
                    await self.telegram_app.stop()
                except Exception as e:
                    logger.error(f"Error stopping Telegram app: {e}")

    # =========================
    # TELEGRAM COMMAND HANDLERS 
    # =========================
    
    async def telegram_start(self, update, context):
        """Handler untuk /start - Professional welcome"""
        welcome_msg = (
            "🚀 *TRADING BOT AKTIF*\n\n"
            "✅ Bot sudah siap dan commands tersedia!\n\n"
            "📋 *COMMANDS TERSEDIA:*\n"
            "• /start - Start bot\n"
            "• /help - Bantuan\n"
            "• /status - Status bot\n"
            "• /balance - Cek saldo\n"
            "• /equity - Info equity\n"
            "• /risk - Risk management\n"
            "• /performance - Performa trading\n"
            "• /mode - Mode trading\n"
            "• /testnet - Switch testnet\n"
            "• /real - Switch real\n"
            "• /topvolume - Update top volume pairs\n"
            "• /risklevel - Set risk level\n"
            "• /maxop - Set max open positions\n"
            "• /stop - Stop bot\n\n"
            "🤖 Bot siap menerima perintah!"
        )
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    async def telegram_status(self, update, context):
        """Handler untuk /status - Enhanced dengan pro data"""
        try:
            if self.client:
                # Get real-time balance and positions
                balances = await self.client.futures_account_balance()
                balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
                positions = await self.client.futures_position_information()
                active_positions = [p for p in positions if float(p['positionAmt']) != 0]
                
                # Get account info for unrealized P&L
                account_info = await self.client.futures_account()
                total_unrealized_pnl = float(account_info['totalUnrealizedProfit'])
                total_equity = balance + total_unrealized_pnl
                
                # Update equity trader with real data
                if self.equity_trader:
                    self.equity_trader.update_equity(total_equity)
                    stats = self.equity_trader.get_performance_stats()
                    win_rate = stats.get('win_rate', 0)
                    kelly_percentage = stats.get('kelly_suggested_risk', 0) / 100
                else:
                    win_rate = 0.0
                    kelly_percentage = 0.025
                
                mode = "TESTNET" if self.config.is_testnet else "REAL"
                memory_usage = self.process.memory_info().rss / 1024 / 1024
                
                # Enhanced status message with real data
                status_msg = (
                    f"⚡ *BOT STATUS*\n\n"
                    f"💰 Balance: **${balance:.2f}**\n"
                    f"📊 Equity: **${total_equity:.2f}**\n"
                    f"📈 Unrealized P&L: **${total_unrealized_pnl:+.2f}**\n"
                    f"🎯 Active Positions: **{len(active_positions)}**\n"
                    f"🔧 Mode: **{mode}**\n"
                    f"📊 Win Rate: **{win_rate:.1%}**\n"
                    f"🎲 Kelly Risk: **{kelly_percentage:.2%}**\n"
                    f"💾 Memory: **{memory_usage:.1f}MB**\n"
                    f"⚙️ Status: **{'🟢 RUNNING' if self.is_running else '🔴 STOPPED'}**"
                )
                
                await update.message.reply_text(status_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Bot belum connect ke Binance")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def telegram_balance(self, update, context):
        """Handler untuk /balance - Enhanced dengan real data"""
        try:
            if self.client:
                # Get real-time balance and account info
                balances = await self.client.futures_account_balance()
                balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
                account_info = await self.client.futures_account()
                total_unrealized_pnl = float(account_info['totalUnrealizedProfit'])
                total_equity = balance + total_unrealized_pnl
                
                # Update equity trader with real data
                if self.equity_trader:
                    self.equity_trader.update_equity(total_equity)
                    stats = self.equity_trader.get_performance_stats()
                    total_return = stats.get('total_return', 0)
                    initial_balance = self.equity_trader.initial_balance
                else:
                    total_return = 0.0
                    initial_balance = balance  # Fallback
                
                # Calculate growth from initial balance
                growth = total_return
                
                # Enhanced balance message
                mood = "💎" if growth > 10 else "⚡" if growth > 5 else "📈" if growth > 0 else "🛡️"
                balance_msg = (
                    f"💰 *ACCOUNT BALANCE*\n\n"
                    f"{mood} **Current Balance:** ${balance:.2f}\n"
                    f"📊 **Total Equity:** ${total_equity:.2f}\n"
                    f"📈 **Unrealized P&L:** ${total_unrealized_pnl:+.2f}\n"
                    f"📊 **Total Growth:** {growth:+.2f}%\n"
                    f"🏛️ **Initial Capital:** ${initial_balance:.2f}\n"
                    f"💎 **Capital Growth:** ${total_equity - initial_balance:+.2f}"
                )
                
                await update.message.reply_text(balance_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Bot belum connect ke Binance")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def telegram_performance(self, update, context):
        """Handler untuk /performance - Show real trading stats"""
        try:
            if self.equity_trader:
                # Get real performance stats from equity trader
                stats = self.equity_trader.get_performance_stats()
                
                if stats['total_trades'] > 0:
                    performance_msg = (
                        f"📊 *TRADING PERFORMANCE*\n\n"
                        f"🎯 **Total Trades:** {stats['total_trades']}\n"
                        f"✅ **Winning Trades:** {int(stats['win_rate'] * stats['total_trades'])}\n"
                        f"📈 **Win Rate:** {stats['win_rate']:.1%}\n"
                        f"💰 **Total Return:** {stats['total_return']:+.2f}%\n"
                        f"📊 **Avg Profit:** {stats['avg_profit']:+.2f}%\n"
                        f"📉 **Avg Loss:** {stats['avg_loss']:+.2f}%\n"
                        f"🌟 **Best Trade:** {stats['best_trade']:+.2f}%\n"
                        f"🛡️ **Worst Trade:** {stats['worst_trade']:+.2f}%\n"
                        f"🎲 **Kelly Risk:** {stats['kelly_suggested_risk']:.2f}%\n\n"
                        f"🔥 **Current Streak:**\n"
                        f"• Wins: {self.equity_trader.get_consecutive_wins()}\n"
                        f"• Losses: {self.equity_trader.get_consecutive_losses()}"
                    )
                else:
                    performance_msg = (
                        f"📊 *TRADING PERFORMANCE*\n\n"
                        f"🎯 **Total Trades:** 0\n"
                        f"📈 **Win Rate:** 0%\n"
                        f"💰 **Total Return:** 0%\n\n"
                        f"🚀 **Ready for first trade!**\n"
                        f"Bot siap untuk mulai trading dengan modal ${self.equity_trader.initial_balance:.2f}"
                    )
            else:
                performance_msg = "❌ Equity trading system tidak aktif"
            
            await update.message.reply_text(performance_msg, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def telegram_mode(self, update, context):
        """Handler untuk /mode"""
        mode = "TESTNET 🧪" if self.config.is_testnet else "REAL TRADING 🚨"
        await update.message.reply_text(f"Current mode: *{mode}*", parse_mode='Markdown')
    
    async def telegram_testnet(self, update, context):
        """Handler untuk /testnet"""
        self.config.is_testnet = True
        self.config.save_config()
        await update.message.reply_text("✅ Switched to *TESTNET*\nBot will restart automatically", parse_mode='Markdown')
        await self.restart_with_new_mode()
    
    async def telegram_real(self, update, context):
        """Handler untuk /real"""
        self.config.is_testnet = False
        self.config.save_config()
        await update.message.reply_text("🚨 Switched to *REAL TRADING*\nBe careful! Bot restarting...", parse_mode='Markdown')
        await self.restart_with_new_mode()
    
    async def telegram_stop(self, update, context):
        """Handler untuk /stop"""
        await update.message.reply_text("🛑 Professional bot stopping!\nSee you next time! 👋")
        self.is_running = False
    
    async def telegram_help(self, update, context):
        """Handler untuk /help"""
        help_msg = (
            "📖 *BANTUAN TRADING BOT*\n\n"
            "🔧 *COMMAND UTAMA:*\n"
            "• /start - Mulai bot\n"
            "• /status - Status trading\n"
            "• /balance - Saldo akun\n"
            "• /equity - Info equity\n\n"
            "📊 *MONITORING:*\n"
            "• /performance - Performa\n"
            "• /risk - Risk management\n"
            "• /topvolume - Update volume pairs\n\n"
            "⚙️ *PENGATURAN:*\n"
            "• /mode - Cek mode trading\n"
            "• /testnet - Mode testnet\n"
            "• /real - Mode real\n"
            "• /risklevel <level> - Set risk level\n"
            "• /maxop <n> - Set max positions\n\n"
            "🔄 *KONTROL:*\n"
            "• /stop - Stop bot\n\n"
            "� *Tips:* Gunakan /status untuk cek kondisi bot"
        )
        await update.message.reply_text(help_msg, parse_mode='Markdown')
    
    async def telegram_unknown_command(self, update, context):
        """Handler untuk unknown commands"""
        message = (
            "❓ *COMMAND TIDAK DIKENAL*\n\n"
            "Gunakan /help untuk melihat daftar command yang tersedia.\n\n"
            "📋 *Quick Commands:*\n"
            "• /start - Mulai bot\n"
            "• /help - Bantuan\n"
            "• /status - Status bot\n"
            "• /balance - Cek saldo\n\n"
            "💡 Ketik command dengan benar ya!"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def telegram_upgrade(self, update, context):
        """Handler untuk /upgrade - Show performance & upgrade status"""
        try:
            status = self.performance_monitor.get_current_status()
            
            if not status:
                await update.message.reply_text("❌ Performance data tidak tersedia")
                return
            
            metrics = status['metrics']
            current_tier = status['current_tier']
            max_positions = status['max_positions']
            requirements = status['next_upgrade_requirements']
            
            upgrade_msg = (
                f"📊 *PERFORMANCE & UPGRADE STATUS*\n\n"
                f"🎯 Current Tier: {current_tier.upper()}\n"
                f"📈 Max Positions: {max_positions}\n"
                f"💰 Balance: ${metrics['current_balance']:.2f}\n\n"
                f"📊 PERFORMANCE METRICS:\n"
                f"• Total Trades: {metrics['total_trades']}\n"
                f"• Win Rate: {metrics['win_rate']:.1%}\n"
                f"• Profit Factor: {metrics['profit_factor']:.2f}\n"
                f"• Max Drawdown: {metrics['max_drawdown']:.1%}\n"
                f"• Track Record: {metrics['track_record_days']} days\n\n"
            )
            
            if requirements.get('next_tier'):
                next_tier = requirements['next_tier']
                req = requirements['requirements']
                
                upgrade_msg += (
                    f"🚀 NEXT UPGRADE: {next_tier.upper()}\n"
                    f"📋 Requirements:\n"
                    f"• Min Balance: ${req['min_balance']:.0f} "
                    f"({'✅' if req['balance_met'] else '❌'})\n"
                    f"• Min Trades: {req['min_trades']} "
                    f"({'✅' if req['trades_met'] else '❌'})\n"
                    f"• Win Rate: ≥65% "
                    f"({'✅' if metrics['win_rate'] >= 0.65 else '❌'})\n"
                    f"• Profit Factor: ≥1.5 "
                    f"({'✅' if metrics['profit_factor'] >= 1.5 else '❌'})\n"
                    f"• Max Drawdown: ≤10% "
                    f"({'✅' if metrics['max_drawdown'] <= 0.10 else '❌'})\n"
                )
            else:
                upgrade_msg += "🎉 *MAXIMUM TIER REACHED!*\nBot sudah di level tertinggi!"
            
            await update.message.reply_text(upgrade_msg, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def telegram_equity(self, update, context):
        """Handler untuk /equity - Show real equity trading status"""
        try:
            if not self.equity_trader:
                await update.message.reply_text("❌ Equity trading system tidak aktif")
                return
            
            # Update equity real-time
            if self.client:
                balances = await self.client.futures_account_balance()
                balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
                account_info = await self.client.futures_account()
                total_unrealized_pnl = float(account_info['totalUnrealizedProfit'])
                total_equity = balance + total_unrealized_pnl
                self.equity_trader.update_equity(total_equity)
            
            # Get performance stats
            stats = self.equity_trader.get_performance_stats()
            
            # Enhanced equity message with real data
            equity_msg = (
                f"💰 *EQUITY TRADING STATUS*\n\n"
                f"📊 **Current Equity:** ${self.equity_trader.get_current_equity():.2f}\n"
                f"🎯 **Peak Equity:** ${self.equity_trader.get_peak_equity():.2f}\n"
                f"📈 **Total Return:** {stats.get('total_return', 0):+.2f}%\n"
                f"📉 **Current Drawdown:** {self.equity_trader.get_current_drawdown():.2f}%\n"
                f"📊 **Daily P&L:** {self.equity_trader.get_daily_pnl():+.2f}%\n\n"
                f"🎲 **PERFORMANCE:**\n"
                f"• Win Rate: {stats.get('win_rate', 0):.1%}\n"
                f"• Total Trades: {stats.get('total_trades', 0)}\n"
                f"• Consecutive Wins: {self.equity_trader.get_consecutive_wins()}\n"
                f"• Consecutive Losses: {self.equity_trader.get_consecutive_losses()}\n\n"
                f"⚡ **RISK SETTINGS:**\n"
                f"• Risk Level: {self.equity_trader.risk_level.title()}\n"
                f"• Base Risk: {self.equity_trader.base_risk_percent:.1f}%\n"
                f"• Max Risk: {self.equity_trader.max_risk_percent:.1f}%\n"
                f"• Max Drawdown: {self.equity_trader.max_drawdown_percent:.1f}%\n"
                f"• Leverage: {self.equity_trader.leverage}x\n\n"
                f"💡 **Kelly Suggestion:** {stats.get('kelly_suggested_risk', 0):.2f}%\n\n"
                f"🏛️ **Initial Capital:** ${self.equity_trader.initial_balance:.2f}"
            )
            
            await update.message.reply_text(equity_msg, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def telegram_risk(self, update, context):
        """Handler untuk /risk - Show real risk analysis"""
        try:
            if not self.equity_trader:
                await update.message.reply_text("❌ Equity trading system tidak aktif")
                return
            
            # Update equity real-time first
            if self.client:
                balances = await self.client.futures_account_balance()
                balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
                account_info = await self.client.futures_account()
                total_unrealized_pnl = float(account_info['totalUnrealizedProfit'])
                total_equity = balance + total_unrealized_pnl
                self.equity_trader.update_equity(total_equity)
            
            # Check current trading conditions
            should_stop, stop_reason = self.equity_trader.should_stop_trading()
            
            # Calculate adaptive risk for next trade
            adaptive_risk = self.equity_trader.calculate_adaptive_risk()
            
            # Get performance stats
            stats = self.equity_trader.get_performance_stats()
            
            # Enhanced risk message with real data
            risk_msg = (
                f"⚠️ *RISK ANALYSIS*\n\n"
                f"🛡️ **SAFETY STATUS:**\n"
                f"• Trading Status: {'🚨 STOPPED' if should_stop else '✅ ACTIVE'}\n"
                f"• Reason: {stop_reason}\n\n"
                f"📊 **CURRENT RISK:**\n"
                f"• Base Risk: {self.equity_trader.base_risk_percent:.1f}%\n"
                f"• Adaptive Risk: {adaptive_risk:.1f}%\n"
                f"• Current Drawdown: {self.equity_trader.get_current_drawdown():.1f}%\n"
                f"• Daily P&L: {self.equity_trader.get_daily_pnl():+.1f}%\n\n"
                f"🔥 **STREAK INFO:**\n"
                f"• Wins: {self.equity_trader.get_consecutive_wins()}\n"
                f"• Losses: {self.equity_trader.get_consecutive_losses()}\n\n"
                f"🏦 **RISK LIMITS:**\n"
                f"• Max Drawdown: {self.equity_trader.max_drawdown_percent:.1f}%\n"
                f"• Daily Loss Limit: {self.equity_trader.daily_loss_limit:.1f}%\n"
                f"• Portfolio Heat: {self.equity_trader.get_portfolio_heat_limit():.1f}%\n\n"
                f"📈 **PERFORMANCE:**\n"
                f"• Win Rate: {stats.get('win_rate', 0):.1%}\n"
                f"• Total Return: {stats.get('total_return', 0):+.2f}%\n"
                f"• Kelly Risk: {stats.get('kelly_suggested_risk', 0):.2f}%"
            )
            
            await update.message.reply_text(risk_msg, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def telegram_topvolume(self, update, context):
        """Handler /topvolume – ambil 10 pair volume tertinggi & update symbols"""
        try:
            if not self.client:
                await update.message.reply_text("❌ Bot belum connect ke Binance")
                return

            # Ambil saldo untuk hitung tradeable symbols (pakai fungsi bawaan)
            balances = await self.client.futures_account_balance()
            usdt_balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)

            tradeable_symbols = await self.get_tradeable_symbols(usdt_balance)
            if tradeable_symbols:
                self.symbols = tradeable_symbols
                # Simpan ke config jika tersedia
                if isinstance(self.config, dict):
                    self.config['symbols'] = tradeable_symbols
                else:
                    self.config.symbols = tradeable_symbols
                    if hasattr(self.config, 'save_config'):
                        self.config.save_config()

                await update.message.reply_text(
                    f"✅ Symbol list di-update ke 10 volume tertinggi:\n{', '.join(tradeable_symbols)}",
                    parse_mode='Markdown'
                )
                logger.info(f"Symbols updated via /topvolume: {tradeable_symbols}")
            else:
                await update.message.reply_text("⚠️ Balance tidak cukup atau tidak dapat mengambil symbol volume tertinggi")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
            logger.error(f"Error in /topvolume: {e}")
    
    async def telegram_set_risklevel(self, update, context):
        """/risklevel <level> – ubah risk level trading"""
        try:
            args = context.args if hasattr(context, 'args') else []
            if not args:
                await update.message.reply_text(
                    "Format: /risklevel <level>\n\n"
                    "Level yang tersedia:\n"
                    "• ultra_conservative\n"
                    "• conservative\n"
                    "• moderate\n"
                    "• balanced\n"
                    "• professional\n"
                    "• aggressive\n"
                    "• full_aggressive\n\n"
                    "Contoh: /risklevel conservative"
                )
                return

            level = args[0].lower()
            valid_levels = [
                'ultra_conservative', 'conservative', 'moderate', 'balanced',
                'professional', 'aggressive', 'full_aggressive'
            ]
            if level not in valid_levels:
                await update.message.reply_text(f"❌ Level tidak dikenal. Pilih: {', '.join(valid_levels)}")
                return

            # Update config dengan multiple approaches
            success = False
            
            # Method 1: Update dict config
            if isinstance(self.config, dict):
                self.config['risk_level'] = level
                success = True
                logger.info(f"Updated dict config: risk_level = {level}")
            
            # Method 2: Update object config
            else:
                try:
                    self.config.risk_level = level
                    success = True
                    logger.info(f"Updated object config: risk_level = {level}")
                    
                    # Try to save config if method exists
                    if hasattr(self.config, 'save_config'):
                        self.config.save_config()
                        logger.info("Config saved successfully")
                except Exception as e:
                    logger.error(f"Error updating object config: {e}")
            
            # Method 3: Update equity trader if available
            if self.equity_trader:
                try:
                    # Reinitialize equity trader with new risk level
                    self.equity_trader.risk_level = level
                    success = True
                    logger.info(f"Updated equity trader: risk_level = {level}")
                except Exception as e:
                    logger.error(f"Error updating equity trader: {e}")

            if success:
                await update.message.reply_text(
                    f"✅ **Risk level di-set ke {level}**\n\n"
                    f"⚠️ Bot akan menggunakan risk management {level}\n"
                    f"🔄 Perubahan akan aktif segera",
                    parse_mode='Markdown'
                )
                logger.info(f"Risk level updated via /risklevel: {level}")
            else:
                await update.message.reply_text("❌ Gagal mengupdate risk level")
                
        except Exception as e:
            logger.error(f"Error in /risklevel: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def telegram_set_maxop(self, update, context):
        """/maxop <n> – ubah maksimum posisi terbuka"""
        try:
            args = context.args if hasattr(context, 'args') else []
            if not args:
                await update.message.reply_text("Format: /maxop <angka>\nContoh: /maxop 3")
                return

            try:
                n = int(args[0])
                if n <= 0 or n > 10:
                    raise ValueError
            except ValueError:
                await update.message.reply_text("❌ Angka harus 1–10")
                return

            # Update config dengan multiple approaches
            success = False
            
            # Method 1: Update dict config
            if isinstance(self.config, dict):
                self.config['max_open_positions'] = n
                self.config['max_open_trades'] = n  # alias
                success = True
                logger.info(f"Updated dict config: max_open_positions = {n}")
            
            # Method 2: Update object config
            else:
                try:
                    self.config.max_open_positions = n
                    self.config.max_open_trades = n  # alias
                    success = True
                    logger.info(f"Updated object config: max_open_positions = {n}")
                    
                    # Try to save config if method exists
                    if hasattr(self.config, 'save_config'):
                        self.config.save_config()
                        logger.info("Config saved successfully")
                except Exception as e:
                    logger.error(f"Error updating object config: {e}")
            
            # Method 3: Update equity trader if available
            if self.equity_trader:
                try:
                    self.equity_trader.max_open_trades = n
                    success = True
                    logger.info(f"Updated equity trader: max_open_trades = {n}")
                except Exception as e:
                    logger.error(f"Error updating equity trader: {e}")

            if success:
                await update.message.reply_text(
                    f"✅ **Max open positions di-set ke {n}**\n\n"
                    f"📊 Bot sekarang akan maksimal membuka {n} posisi bersamaan\n"
                    f"🔄 Perubahan akan aktif segera",
                    parse_mode='Markdown'
                )
                logger.info(f"Max open positions updated via /maxop: {n}")
            else:
                await update.message.reply_text("❌ Gagal mengupdate max open positions")
                
        except Exception as e:
            logger.error(f"Error in /maxop: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # =========================
    # CORE TRADING FUNCTIONS
    # =========================
    
    async def restart_with_new_mode(self):
        """Restart bot dengan mode baru"""
        try:
            if self.client:
                await self.client.close_connection()
            
            await asyncio.sleep(2)
            await self.init_binance_client()
            
        except Exception as e:
            logger.error(f"Error restarting bot: {e}")
    
    async def get_klines_data(self, symbol: str, interval: str, limit: int = 100) -> list:
        """Get klines data dengan memory optimization"""
        try:
            klines = await self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            # Process and optimize memory usage
            processed_klines = []
            for kline in klines:
                processed_klines.append([
                    kline[0],  # Open time
                    float(kline[1]),  # Open
                    float(kline[2]),  # High
                    float(kline[3]),  # Low
                    float(kline[4]),  # Close
                    float(kline[5])   # Volume
                ])
            
            return processed_klines
            
        except Exception as e:
            logger.error(f"Error getting klines data: {e}")
            return []
    
    async def execute_trade_pro(self, symbol: str, entry_analysis: Dict[str, Any], klines_data: list = None) -> bool:
        """Execute trade dengan professional analysis dan equity-based sizing"""
        try:
            action = entry_analysis['action']
            confidence = entry_analysis['confidence']
            reason = entry_analysis['reason']
            pro_analysis = entry_analysis.get('pro_analysis', {})
            position_sizing = entry_analysis.get('position_sizing', {})
            
            # Get account balance dan update equity
            balances = await self.client.futures_account_balance()
            balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
            
            # Get current price for position calculation
            ticker = await self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            # Use Enhanced Equity Position Sizing if available
            if self.equity_trader:
                # Update equity dengan real-time balance
                account_info = await self.client.futures_account()
                total_unrealized_pnl = float(account_info['totalUnrealizedProfit'])
                total_equity = balance + total_unrealized_pnl
                self.equity_trader.update_equity(total_equity)
                
                # Calculate stop loss price (simplified: 1% from entry)
                if action == "long":
                    stop_loss_price = current_price * 0.99  # 1% below for long
                else:
                    stop_loss_price = current_price * 1.01  # 1% above for short
                
                # Check if we should enter this trade
                can_trade, trade_reason = self.equity_trader.should_enter_trade(symbol, confidence / 100)
                if not can_trade:
                    logger.info(f"[EQUITY] Trade rejected: {trade_reason}")
                    await self.telegram.send_casual_message(f"❌ Trade ditolak: {trade_reason}")
                    return False
                
                # Check if we should use auto leverage
                if hasattr(self.equity_trader, 'use_auto_leverage') and self.equity_trader.use_auto_leverage:
                    # Use auto leverage for balance $10+
                    market_data = {
                        'volatility': self._calculate_market_volatility(symbol, klines_data) if klines_data else 0.03
                    }
                    leverage = int(self.position_sizing.calculate_auto_leverage(symbol, balance, market_data))
                    
                    # Ensure minimum notional for auto leverage
                    min_notional = 5.0
                    risk_pct = self.equity_trader.base_risk_percent / 100
                    risk_amount = balance * risk_pct
                    
                    if (risk_amount * leverage) < min_notional:
                        # Adjust leverage to meet minimum notional
                        required_leverage = min_notional / risk_amount
                        leverage = max(int(required_leverage) + 1, leverage)
                        logger.info(f"[AUTO] Adjusted leverage to {leverage}x to meet minimum notional")
                    
                    quantity = (risk_amount * leverage) / current_price
                    risk_percent = risk_pct * 100
                    
                    logger.info(f"[AUTO] Position size: {quantity:.6f} {symbol.replace('USDT', '')} | Risk: {risk_percent:.2f}% | Auto Leverage: {leverage}x")
                    
                else:
                    # Use fixed leverage (10x) for balance < $10
                    quantity, risk_percent = self.equity_trader.calculate_position_size_with_leverage(
                        current_price, stop_loss_price, symbol, confidence / 100
                    )
                    leverage = self.equity_trader.leverage
                    
                    logger.info(f"[EQUITY] Position size: {quantity:.6f} {symbol.replace('USDT', '')} | Risk: {risk_percent:.2f}% | Fixed Leverage: {leverage}x")
                
            else:
                # Fallback to original position sizing
                from bot_modules.risk.position_sizing import dynamic_fraction
                risk_pct = position_sizing.get('risk_percentage', dynamic_fraction(balance))
                
                # Calculate auto leverage based on market conditions & 5-USDT notional rule
                market_data = {
                    'volatility': self._calculate_market_volatility(symbol, klines_data) if klines_data else 0.03
                }
                leverage = int(self.position_sizing.calculate_auto_leverage(
                    symbol,
                    balance,
                    market_data,
                    risk_amount=risk_amount,
                    price=current_price
                ))
                
                risk_amount = balance * risk_pct
                quantity = (risk_amount * leverage) / current_price
                
                logger.info(f"[LEGACY] Position size: {quantity:.6f} | Risk: {risk_pct:.2%} | Leverage: {leverage}x")
            
            # Check minimum quantity with safe access
            exchange_info = await self.client.futures_exchange_info()
            symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
            if not symbol_info:
                logger.error(f"Symbol {symbol} not found in exchange info")
                return False
                
            lot_size_filters = [f for f in symbol_info.get('filters', []) if f.get('filterType') == 'LOT_SIZE']
            if not lot_size_filters:
                logger.error(f"No LOT_SIZE filter found for {symbol}")
                return False
                
            min_qty = float(lot_size_filters[0].get('minQty', '0.001'))
            step_size = float(lot_size_filters[0].get('stepSize', '0.001'))
            
            if quantity < min_qty:
                await self.telegram.send_casual_message(f"⚠️ Quantity too small: {quantity:.6f} < {min_qty}")
                return False
            
            # Cek minimum notional (Binance: $5)
            notional = quantity * current_price
            min_notional = 5.0
            if notional < min_notional:
                await self.telegram.send_casual_message(
                    f"⚠️ Notional too small: {notional:.2f} < {min_notional} (quantity: {quantity}, price: {current_price})"
                )
                return False
            
            # Round quantity properly
            quantity = round(quantity / step_size) * step_size
            
            # Set leverage
            await self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            
            # Place order
            side = SIDE_BUY if action == "long" else SIDE_SELL
            order = await self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            # Send professional notification
            message = self.telegram.get_entry_message(action, symbol, confidence, reason, pro_analysis)
            await self.telegram.send_casual_message(message)
            
            # Store entry data untuk professional exit
            self.active_entries[symbol] = {
                'entry_analysis': pro_analysis,
                'entry_time': datetime.now(),
                'entry_price': current_price,
                'position_sizing': position_sizing
            }
            
            # Log dengan risk yang appropriate
            if self.equity_trader:
                logger.info(f"PRO TRADE: {action} {symbol} qty:{quantity:.6f} leverage:{leverage}x risk:{risk_percent:.2f}%")
            else:
                logger.info(f"PRO TRADE: {action} {symbol} qty:{quantity:.6f} leverage:{leverage}x risk:{risk_pct:.2%}")
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Binance API Error in trade execution: {e}")
            await self.telegram.send_casual_message(f"❌ Binance API Error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error executing professional trade: {e}")
            await self.telegram.send_casual_message(f"❌ Trade error: {str(e)}")
            return False
    
    async def close_position_pro(self, symbol: str, position_data: dict, exit_analysis: Dict = None) -> bool:
        """Close position dengan professional exit analysis"""
        try:
            position_amt = float(position_data['positionAmt'])
            
            if position_amt == 0:
                return True
            
            # Determine side for closing
            side = SIDE_SELL if position_amt > 0 else SIDE_BUY
            quantity = abs(position_amt)
            
            # Close position
            order = await self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity,
                reduceOnly=True
            )
            
            # Calculate profit
            entry_price = float(position_data['entryPrice'])
            current_price = float(position_data['markPrice'])
            
            if position_amt > 0:  # LONG
                profit_pct = (current_price - entry_price) / entry_price
            else:  # SHORT
                profit_pct = (entry_price - current_price) / entry_price
            
            # Get exit details
            exit_reason = exit_analysis.get('reason', 'Professional exit') if exit_analysis else 'Smart exit'
            urgency = exit_analysis.get('urgency', 'NONE') if exit_analysis else 'NONE'
            
            # Send professional notification
            side_text = "LONG" if position_amt > 0 else "SHORT"
            message = self.telegram.get_exit_message(symbol, side_text, profit_pct, exit_reason, urgency)
            await self.telegram.send_casual_message(message)
            
            # Update trade history untuk Kelly calculation
            if symbol in self.active_entries:
                trade_data = {
                    'symbol': symbol,
                    'profit_pct': profit_pct,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'exit_reason': exit_reason,
                    'timestamp': datetime.now()
                }
                self.smart_entry.add_trade_to_history(trade_data)
                
                # Add to performance monitor for auto-upgrade tracking
                self.performance_monitor.add_trade(trade_data)
                
                # Update equity trader with trade result
                if self.equity_trader:
                    self.equity_trader.add_trade_result(profit_pct * 100)  # Convert to percentage
                    logger.info(f"Equity updated: Trade result {profit_pct:.2%} added to performance tracking")

                    # Check if equity level change requires config update
                    if self.equity_trader.update_equity(balance := (float(position_data['unRealizedProfit']) + float(position_data['isolatedWallet']))):
                        dyn = self.equity_trader.get_dynamic_strategy()
                        logger.info(f"[DYNAMIC] Strategy tier changed ⇒ {dyn}")
                        for k, v in dyn.items():
                            setattr(self.config, k, v) if not isinstance(self.config, dict) else self.config.__setitem__(k, v)
                
                del self.active_entries[symbol]
            
            logger.info(f"PRO CLOSE: {symbol} profit: {profit_pct:.3%} reason: {exit_reason}")
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Binance API Error in position closing: {e}")
            await self.telegram.send_casual_message(f"❌ Binance API Error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error closing position professionally: {e}")
            return False
    
    def _calculate_market_volatility(self, symbol: str, klines_data: list) -> float:
        """Calculate market volatility for auto leverage"""
        try:
            if not klines_data or len(klines_data) < 20:
                return 0.03  # Default moderate volatility
            
            # Calculate price changes
            prices = [float(k[4]) for k in klines_data]  # Close prices
            returns = []
            
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    returns.append(abs((prices[i] - prices[i-1]) / prices[i-1]))
            
            if not returns:
                return 0.03
            
            # Calculate volatility as standard deviation of returns
            volatility = np.std(returns) if len(returns) > 1 else 0.03
            
            logger.info(f"Market volatility for {symbol}: {volatility:.4f}")
            return volatility
            
        except Exception as e:
            logger.error(f"Error calculating market volatility: {e}")
            return 0.03  # Default moderate volatility

    def optimize_memory(self):
        """Memory optimization untuk VPS 1GB"""
        self.memory_optimization_counter += 1
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        
        # More frequent memory checks for VPS optimization
        if self.memory_optimization_counter % 50 == 0:  # Check every 50 iterations
            # Clear old data more aggressively
            if len(self.last_price_data) > 500:  # Reduced from 1000
                self.last_price_data.clear()
            
            # Clear any cached data
            if hasattr(self, 'cached_klines'):
                self.cached_klines.clear()
            
            # Garbage collection
            gc.collect()
            
            # Log memory usage
            logger.info(f"Memory optimized: {memory_mb:.1f}MB")
            
            if memory_mb > 600:  # Lowered threshold from 800MB
                logger.warning(f"High memory usage: {memory_mb:.1f}MB")
                
                # Additional cleanup for high memory usage
                if hasattr(self, 'performance_monitor'):
                    self.performance_monitor._cleanup_old_data()

        # Critical memory threshold - DISABLED AUTO-REBOOT
        if memory_mb > 600:
            logger.error(f"Memory usage critical {memory_mb:.1f}MB – DISABLED AUTO-REBOOT")
            try:
                # Inform via Telegram about memory issue
                asyncio.create_task(self.telegram.send_casual_message(
                    f"⚠️ *Memory Warning*\n"
                    f"VPS memory: {memory_mb:.1f}MB\n"
                    f"Auto-reboot disabled for safety\n"
                    f"Bot will continue trading"
                ))
            except Exception:
                pass
            
            # Force aggressive cleanup instead of reboot
            try:
                # Clear all caches
                if hasattr(self, 'last_price_data'):
                    self.last_price_data.clear()
                if hasattr(self, 'cached_klines'):
                    self.cached_klines.clear()
                if hasattr(self, 'performance_monitor'):
                    self.performance_monitor._cleanup_old_data()
                
                # Force garbage collection
                gc.collect()
                
                logger.info(f"Performed aggressive memory cleanup: {self.process.memory_info().rss / 1024 / 1024:.1f}MB")
                
            except Exception as e:
                logger.error(f"Failed to cleanup memory: {e}")
    
    async def trading_loop(self):
        """PRO TRADER Main Trading Loop - Modular & Intelligent"""
        logger.info("Starting PRO TRADER modular loop...")
        
        # Send startup message
        try:
            startup_message = self.telegram.get_startup_message()
            await self.telegram.send_casual_message(startup_message)
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")
        
        # Check if Binance client is available
        if not self.client:
            logger.warning("Binance client not available, running in Telegram-only mode")
            while self.is_running:
                await asyncio.sleep(10)
            return
        
        while self.is_running:
            try:
                # Memory optimization
                self.optimize_memory()

                # Check for auto-upgrade based on performance
                upgrade_config = self.performance_monitor.check_and_upgrade()
                if upgrade_config:
                    # Apply auto-upgrade
                    self.config.max_open_positions = upgrade_config['config']['max_open_trades']
                    self.config.max_open_trades = upgrade_config['config']['max_open_trades']  # Keep both for compatibility
                    self.config.confidence_threshold = upgrade_config['config']['confidence_threshold']
                    # Send upgrade notification
                    upgrade_msg = (
                        f"🚀 *AUTO UPGRADE ACTIVATED!*\n\n"
                        f"Tier: {upgrade_config['tier']}\n"
                        f"Max Positions: {upgrade_config['max_positions']}\n"
                        f"Reason: {upgrade_config['reason']}\n\n"
                        f"Bot akan trading dengan {upgrade_config['max_positions']} posisi!"
                    )
                    await self.telegram.send_casual_message(upgrade_msg)
                    logger.info(f"AUTO UPGRADE: {upgrade_config['tier']} - {upgrade_config['max_positions']} positions")

                # Check if we have tradeable symbols
                if not self.symbols:
                    logger.warning("No tradeable symbols available, skipping trading")
                    await asyncio.sleep(60)
                    continue

                # Fetch all positions once for heat & limits
                all_positions = await self.client.futures_position_information()
                open_positions = [p for p in all_positions if float(p['positionAmt']) != 0]

                # Monitor all tradeable symbols
                for symbol in self.symbols:
                    # Filter position for this symbol
                    symbol_positions = [p for p in open_positions if p['symbol'] == symbol]
                    
                    # Check portfolio heat - use actual balance from Binance
                    balances = await self.client.futures_account_balance()
                    current_balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
                    portfolio_heat = self.position_sizing.get_portfolio_heat(open_positions, current_balance)
                    if portfolio_heat['max_heat_reached']:
                        logger.info(f"Portfolio heat limit reached: {portfolio_heat['total_heat']:.1%}")
                        continue
                    
                    # Get market data
                    timeframe = self.config.get('timeframe', '1h') if isinstance(self.config, dict) else getattr(self.config, 'timeframe', '1h')
                    klines_data = await self.get_klines_data(symbol, timeframe)
                    if not klines_data:
                        logger.warning(f"No klines data for {symbol}")
                        continue
                    
                    # Check exit conditions first
                    for position in symbol_positions:
                        exit_analysis = self.smart_exit.should_exit(
                            position, 
                            float(position['markPrice']), 
                            klines_data, 
                            self.active_entries.get(symbol, {})
                        )
                        
                        if exit_analysis['action'] == 'close':
                            await self.close_position_pro(symbol, position, exit_analysis)
                    
                    # Check entry conditions with smart position management
                    current_positions_count = len(open_positions)
                    symbol_positions_count = len(symbol_positions)
                    
                    # Check if we can add more positions
                    max_positions = self.config.get('max_open_positions', 1) if isinstance(self.config, dict) else getattr(self.config, 'max_open_positions', 1)
                    can_add_position = current_positions_count < max_positions
                    
                    if can_add_position:
                        entry_analysis = await self.smart_entry.analyze_entry(klines_data)
                        
                        # Determine entry type based on confidence and existing positions
                        high_confidence_threshold = self.config.get('high_confidence_threshold', 80) if isinstance(self.config, dict) else getattr(self.config, 'high_confidence_threshold', 80)
                        confidence_threshold = self.config.get('confidence_threshold', 70) if isinstance(self.config, dict) else getattr(self.config, 'confidence_threshold', 70)
                        
                        is_high_confidence = entry_analysis['confidence'] >= high_confidence_threshold
                        is_normal_confidence = entry_analysis['confidence'] >= confidence_threshold
                        
                        # Check if this is a valid entry
                        can_entry = False
                        entry_type = "normal"
                        
                        if current_positions_count == 0:
                            # First position - normal confidence is enough
                            can_entry = is_normal_confidence and entry_analysis['action'] in ['long', 'short']
                            entry_type = "normal"
                        elif current_positions_count == 1:
                            # Second position - need high confidence and different symbol
                            if getattr(self.config, 'different_symbols_only', True):
                                # Check if we already have a position in this symbol
                                existing_symbols = [p['symbol'] for p in open_positions]
                                if symbol not in existing_symbols and is_high_confidence:
                                    can_entry = entry_analysis['action'] in ['long', 'short']
                                    entry_type = "high_confidence"
                            else:
                                # Allow same symbol if different_symbols_only is false
                                can_entry = is_high_confidence and entry_analysis['action'] in ['long', 'short']
                                entry_type = "high_confidence"
                        elif current_positions_count == 2:
                            # Third position - need very high confidence and different symbol
                            if getattr(self.config, 'different_symbols_only', True):
                                # Check if we already have a position in this symbol
                                existing_symbols = [p['symbol'] for p in open_positions]
                                if symbol not in existing_symbols and entry_analysis['confidence'] >= 75:
                                    can_entry = entry_analysis['action'] in ['long', 'short']
                                    entry_type = "very_high_confidence"
                            else:
                                # Allow same symbol if different_symbols_only is false
                                can_entry = entry_analysis['confidence'] >= 75 and entry_analysis['action'] in ['long', 'short']
                                entry_type = "very_high_confidence"
                        
                        if can_entry:
                            # Check portfolio heat limit
                            portfolio_heat = self.position_sizing.get_portfolio_heat(open_positions, current_balance)
                            heat_limit = getattr(self.config, 'portfolio_heat_limit', 10) / 100
                            
                            if portfolio_heat['total_heat'] < heat_limit:
                                success = await self.execute_trade_pro(symbol, entry_analysis, klines_data)
                                if success:
                                    logger.info(f"PRO TRADE EXECUTED: {entry_type.upper()} {entry_analysis['action']} {symbol} (Confidence: {entry_analysis['confidence']:.1f}%)")
                            else:
                                logger.info(f"Portfolio heat limit reached: {portfolio_heat['total_heat']:.1%} >= {heat_limit:.1%}")
                
                # Sleep between iterations - OPTIMIZED for faster response
                await asyncio.sleep(10)  # Reduced from 15s to 10s for faster trading
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await self.telegram.send_casual_message(f"❌ Error: {str(e)}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start bot: run Telegram polling and trading loop in parallel"""
        self.is_running = True
        
        # Initialize Binance first (but don't stop if it fails)
        success = await self.init_binance_client()
        if not success:
            logger.warning("Binance client failed to initialize, but continuing with Telegram...")
        
        # Initialize Telegram (this is important for commands)
        await self.init_telegram_bot()
        
        # Run both Telegram polling and trading loop in parallel
        # If Binance failed, trading loop will handle it gracefully
        await asyncio.gather(
            self.start_telegram_polling(),
            self.trading_loop()
        )
    
    async def stop(self):
        """Stop the bot gracefully"""
        try:
            self.is_running = False
            
            # Stop Telegram app properly
            if self.telegram_app:
                try:
                    await self.telegram_app.updater.stop()
                    await self.telegram_app.stop()
                    logger.info("Telegram app stopped")
                except Exception as e:
                    logger.error(f"Error stopping Telegram app: {e}")
            
            # Close Binance connection
            if self.client:
                await self.client.close_connection()
                logger.info("Binance connection closed")
            
            # Send final message
            try:
                await self.telegram.send_casual_message("🛑 *Pro Trader Bot Stopped*\nSee you next time! 👋")
            except Exception as e:
                logger.error(f"Error sending final message: {e}")
                
            logger.info("Bot stopped gracefully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

# =========================
# MAIN EXECUTION
# =========================

async def main():
    """Main function untuk menjalankan bot"""
    bot = BinanceFuturesProBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")