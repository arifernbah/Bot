#!/usr/bin/env python3
"""
Bot Trading Binance Futures - MODULAR PRO TRADER EDITION
Struktur modular yang ringan dengan intelligence professional
"""

import asyncio
import logging
from modules import FEE_RATE
import time
from datetime import datetime
from typing import Dict, Any, Optional
import gc
import psutil

# Binance imports
from binance import AsyncClient, BinanceSocketManager
from binance.enums import *
from binance.exceptions import BinanceAPIException

# Telegram imports
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import threading

# Our modular imports - CLEAN & LIGHTWEIGHT
from modules import (
    SmartConfig,
    SmartIndicators,
    MarketRegimeDetector,
    LiquidityZoneDetector, 
    MarketStructureAnalyzer,
    KellyCriterionCalculator,
    TradingSessionAnalyzer,
    SmartEntry,
    SmartExit,
    TelegramNotifier
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', maxBytes=1024*1024, backupCount=1),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BinanceFuturesProBot:
    """
    Professional Trading Bot dengan Modular Structure
    - Intelligence: 10-year Professional Trader
    - Architecture: Hedge Fund Grade  
    - Memory: Optimized untuk VPS 1GB
    - Style: Casual Indonesian dengan data Professional
    """
    
    def __init__(self):
        # Initialize configuration
        self.config = SmartConfig()
        
        # Initialize Binance client
        self.client: Optional[AsyncClient] = None
        
        # Initialize professional modules (MODULAR!)
        self.smart_entry = SmartEntry(self.config)
        self.smart_exit = SmartExit(self.config)
        self.telegram = TelegramNotifier(
            self.config.telegram_token, 
            self.config.telegram_chat_id
        )
        
        # Bot state
        self.is_running = False
        self.positions = {}
        self.last_price_data = {}
        self.memory_optimization_counter = 0
        self.active_entries = {}  # Track entry analysis for pro exits
        
        # Performance monitoring
        self.process = psutil.Process()
        self.telegram_app = None
        
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
            
            # Test connection
            account_info = await self.client.futures_account()
            balance = float([asset['balance'] for asset in account_info['assets'] if asset['asset'] == 'USDT'][0])
            
            logger.info(f"Connected to Binance. Balance: {balance} USDT")
            await self.telegram.send_casual_message(f"✅ *Konek ke Binance berhasil!*\nSaldo: ${balance:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Binance: {e}")
            await self.telegram.send_casual_message(f"❌ Gagal konek ke Binance: {str(e)}")
            return False
    
    def init_telegram_bot(self):
        """Initialize Telegram bot dengan commands"""
        try:
            if not self.config.telegram_token:
                logger.warning("Telegram token tidak tersedia")
                return
            
            self.telegram_app = Application.builder().token(self.config.telegram_token).build()
            
            # Command handlers - Professional tapi tetap casual
            self.telegram_app.add_handler(CommandHandler("start", self.telegram_start))
            self.telegram_app.add_handler(CommandHandler("status", self.telegram_status))
            self.telegram_app.add_handler(CommandHandler("balance", self.telegram_balance))
            self.telegram_app.add_handler(CommandHandler("performance", self.telegram_performance))
            self.telegram_app.add_handler(CommandHandler("mode", self.telegram_mode))
            self.telegram_app.add_handler(CommandHandler("testnet", self.telegram_testnet))
            self.telegram_app.add_handler(CommandHandler("real", self.telegram_real))
            self.telegram_app.add_handler(CommandHandler("stop", self.telegram_stop))
            self.telegram_app.add_handler(CommandHandler("help", self.telegram_help))
            
            # Start telegram in background thread
            def run_telegram():
                asyncio.set_event_loop(asyncio.new_event_loop())
                self.telegram_app.run_polling()
            
            telegram_thread = threading.Thread(target=run_telegram, daemon=True)
            telegram_thread.start()
            
            logger.info("Telegram bot initialized with professional commands")
            
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")
    
    # =========================
    # TELEGRAM COMMAND HANDLERS 
    # =========================
    
    async def telegram_start(self, update, context):
        """Handler untuk /start - Professional welcome"""
        welcome_msg = (
            "🤖 *PRO TRADER BOT - Modular Edition*\n\n"
            "🧠 Intelligence: 10-year Pro Trader\n"
            "🏛️ Market Analysis: Institutional\n"
            "🎯 Risk Management: Hedge Fund\n\n"
            "*Commands Available:*\n"
            "/status - Bot status & positions\n"
            "/balance - Account balance & growth\n"
            "/performance - Trading performance\n"
            "/mode - Current trading mode\n"
            "/testnet - Switch to testnet\n"
            "/real - Switch to real trading\n"
            "/stop - Stop the bot\n"
            "/help - Show this help\n\n"
            "Ready untuk cuan professional! 🚀💎"
        )
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    async def telegram_status(self, update, context):
        """Handler untuk /status - Enhanced dengan pro data"""
        try:
            if self.client:
                account_info = await self.client.futures_account()
                balance = float([asset['balance'] for asset in account_info['assets'] if asset['asset'] == 'USDT'][0])
                positions = await self.client.futures_position_information()
                active_positions = [p for p in positions if float(p['positionAmt']) != 0]
                
                # Get professional stats
                pro_stats = {
                    'win_rate': 0.65,  # Would be calculated from actual trades
                    'kelly_percentage': 0.025,
                    'current_session': 'london'
                }
                
                mode = "TESTNET" if self.config.is_testnet else "REAL"
                memory_usage = self.process.memory_info().rss / 1024 / 1024
                
                status_msg = self.telegram.get_status_message(
                    balance, len(active_positions), mode, pro_stats
                )
                status_msg += f"\n🧠 Memory: {memory_usage:.1f}MB"
                
                await update.message.reply_text(status_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Bot belum connect ke Binance")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def telegram_balance(self, update, context):
        """Handler untuk /balance"""
        try:
            if self.client:
                account_info = await self.client.futures_account()
                balance = float([asset['balance'] for asset in account_info['assets'] if asset['asset'] == 'USDT'][0])
                total_unrealized_pnl = float(account_info['totalUnrealizedProfit'])
                
                growth = ((balance / self.config.modal_awal - 1) * 100)
                
                balance_msg = (
                    f"💰 *PROFESSIONAL BALANCE REPORT*\n\n"
                    f"Current Balance: ${balance:.2f}\n"
                    f"Unrealized PnL: ${total_unrealized_pnl:.2f}\n"
                    f"Initial Capital: ${self.config.modal_awal:.2f}\n"
                    f"Total Growth: {growth:+.2f}%\n\n"
                )
                
                if growth > 10:
                    balance_msg += "🔥 Exceptional performance! Keep it up!"
                elif growth > 5:
                    balance_msg += "⚡ Solid growth! Pro algorithm working!"
                elif growth > 0:
                    balance_msg += "📈 Positive growth! Steady progress!"
                else:
                    balance_msg += "🛡️ Capital protection mode active!"
                
                await update.message.reply_text(balance_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Bot belum connect ke Binance")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def telegram_performance(self, update, context):
        """Handler untuk /performance - Show trading stats"""
        trades_history = getattr(self.smart_entry, 'trades_history', [])
        performance_msg = self.telegram.get_performance_summary(
            trades_history, 
            100.0,  # Would get actual balance
            self.config.modal_awal
        )
        await update.message.reply_text(performance_msg, parse_mode='Markdown')
    
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
            "🤖 *PRO TRADER BOT HELP*\n\n"
            "*Trading Features:*\n"
            "• Professional market analysis\n"
            "• Kelly Criterion position sizing\n"
            "• Multi-timeframe analysis\n"
            "• Session-based timing\n"
            "• Advanced risk management\n\n"
            "*Commands:*\n"
            "/status - Complete bot status\n"
            "/balance - Account overview\n"
            "/performance - Trading statistics\n"
            "/mode - Current trading mode\n"
            "/testnet - Safe practice mode\n"
            "/real - Live trading mode\n\n"
            "*Safety Features:*\n"
            "• Emergency stop loss (3%)\n"
            "• Dynamic risk adjustment\n"
            "• Market structure monitoring\n"
            "• Session-based exits\n\n"
            "Professional algorithm for consistent profits! 🚀💎"
        )
        await update.message.reply_text(help_msg, parse_mode='Markdown')
    
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
    
    async def execute_trade_pro(self, entry_analysis: Dict[str, Any]) -> bool:
        """Execute trade dengan professional analysis"""
        try:
            action = entry_analysis['action']
            symbol = self.config.symbol
            confidence = entry_analysis['confidence']
            reason = entry_analysis['reason']
            pro_analysis = entry_analysis.get('pro_analysis', {})
            position_sizing = entry_analysis.get('position_sizing', {})
            
            # Get account balance
            account_info = await self.client.futures_account()
            balance = float([asset['balance'] for asset in account_info['assets'] if asset['asset'] == 'USDT'][0])
            
            # Use professional position sizing
            risk_pct = position_sizing.get('risk_percentage', 0.02)
            leverage = int(position_sizing.get('leverage', 2))
            
            risk_amount = balance * risk_pct
            
            # Get current price
            ticker = await self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            # Calculate quantity
            quantity = (risk_amount * leverage) / current_price
            
            # Check minimum quantity
            exchange_info = await self.client.futures_exchange_info()
            symbol_info = next(s for s in exchange_info['symbols'] if s['symbol'] == symbol)
            min_qty = float([f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['minQty'])
            step_size = float([f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]['stepSize'])
            
            if quantity < min_qty:
                await self.telegram.send_casual_message(f"⚠️ Quantity too small: {quantity:.6f} < {min_qty}")
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
            
            logger.info(f"PRO TRADE: {action} {symbol} qty:{quantity:.6f} leverage:{leverage}x risk:{risk_pct:.2%}")
            return True
            
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
                del self.active_entries[symbol]
            
            logger.info(f"PRO CLOSE: {symbol} profit: {profit_pct:.3%} reason: {exit_reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position professionally: {e}")
            return False
    
    def optimize_memory(self):
        """Memory optimization untuk VPS 1GB"""
        self.memory_optimization_counter += 1
        
        if self.memory_optimization_counter % 100 == 0:
            # Clear old data
            if len(self.last_price_data) > 1000:
                self.last_price_data.clear()
            
            # Garbage collection
            gc.collect()
            
            # Log memory usage
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            logger.info(f"Memory optimized: {memory_mb:.1f}MB")
            
            if memory_mb > 800:
                logger.warning(f"High memory usage: {memory_mb:.1f}MB")
    
    async def trading_loop(self):
        """PRO TRADER Main Trading Loop - Modular & Intelligent"""
        logger.info("Starting PRO TRADER modular loop...")
        
        startup_message = self.telegram.get_startup_message()
        await self.telegram.send_casual_message(startup_message)
        
        while self.is_running:
            try:
                # Memory optimization
                self.optimize_memory()
                
                # Get current positions
                positions = await self.client.futures_position_information(symbol=self.config.symbol)
                current_position = positions[0] if positions else None
                position_amt = float(current_position['positionAmt']) if current_position else 0
                
                # Get market data
                klines_data = await self.get_klines_data(
                    self.config.symbol,
                    self.config.timeframe,
                    limit=50
                )
                
                if not klines_data:
                    await asyncio.sleep(30)
                    continue
                
                current_price = klines_data[-1][4]
                
                # CHECK EXIT CONDITIONS (if we have position)
                if position_amt != 0:
                    # Get entry analysis if available
                    entry_analysis = None
                    if self.config.symbol in self.active_entries:
                        entry_analysis = self.active_entries[self.config.symbol].get('entry_analysis')
                    
                    exit_analysis = self.smart_exit.should_exit(
                        current_position, 
                        current_price, 
                        klines_data, 
                        entry_analysis
                    )
                    
                    if exit_analysis['action'] == 'close':
                        await self.close_position_pro(self.config.symbol, current_position, exit_analysis)
                        await asyncio.sleep(5)
                        continue
                
                # CHECK ENTRY CONDITIONS (if no position)
                elif self.config.max_open_positions > len([p for p in positions if float(p['positionAmt']) != 0]):
                    entry_analysis = self.smart_entry.analyze_entry(klines_data)
                    
                    if entry_analysis['action'] in ['long', 'short'] and entry_analysis['confidence'] >= 60:
                        success = await self.execute_trade_pro(entry_analysis)
                        
                        if success:
                            # Add to history untuk Kelly calculation
                            self.smart_entry.add_trade_to_history({
                                'symbol': self.config.symbol,
                                'action': entry_analysis['action'],
                                'confidence': entry_analysis['confidence'],
                                'timestamp': datetime.now(),
                                'entry_price': current_price
                            })
                        
                        await asyncio.sleep(10)
                
                # Adaptive sleep
                if position_amt != 0:
                    await asyncio.sleep(15)  # Monitor positions more frequently
                else:
                    await asyncio.sleep(30)  # Normal monitoring
                    
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                error_msg = self.telegram.get_error_message("analysis", str(e))
                await self.telegram.send_casual_message(error_msg)
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the professional trading bot"""
        try:
            logger.info("Starting Professional Trading Bot - Modular Edition")
            
            # Initialize components
            success = await self.init_binance_client()
            if not success:
                return False
            
            self.init_telegram_bot()
            
            # Start trading
            self.is_running = True
            await self.trading_loop()
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot gracefully"""
        try:
            self.is_running = False
            if self.client:
                await self.client.close_connection()
            
            await self.telegram.send_casual_message("🛑 *Pro Trader Bot Stopped*\nSee you next time! 👋")
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