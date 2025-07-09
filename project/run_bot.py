#!/usr/bin/env python3
"""
Runner Script untuk Bot Trading Binance Futures
Script sederhana untuk menjalankan bot dengan monitoring
"""

import asyncio
import os
import sys
import signal
import time
from datetime import datetime

def check_config():
    """Check apakah konfigurasi sudah ada"""
    if not os.path.exists("bot_config.json"):
        print("❌ File konfigurasi tidak ditemukan!")
        print("Jalankan setup dulu: python setup_bot.py")
        return False
    
    print("✅ Konfigurasi ditemukan")
    return True

def show_startup_info():
    """Show startup information"""
    print("=" * 60)
    print("🤖 BOT TRADING BINANCE FUTURES")
    print("📅 Optimized untuk VPS 1GB RAM dengan Modal $5")
    print("=" * 60)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📱 Control via Telegram:")
    print("   /status - Status bot")
    print("   /balance - Cek saldo") 
    print("   /testnet - Mode testnet")
    print("   /real - Mode real trading")
    print("   /stop - Stop bot")
    print("=" * 60)

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Bot stopping...")
    print("Sampai jumpa! 👋")
    sys.exit(0)

async def run_bot_with_restart():
    """Run bot dengan auto-restart jika error"""
    restart_count = 0
    max_restarts = 5
    
    while restart_count < max_restarts:
        try:
            # Import dan jalankan bot
            from bot_binance_futures import BinanceFuturesBot
            
            print(f"🚀 Starting bot (attempt {restart_count + 1})...")
            bot = BinanceFuturesBot()
            await bot.start()
            
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
            break
        except Exception as e:
            restart_count += 1
            print(f"\n❌ Bot error: {e}")
            
            if restart_count < max_restarts:
                wait_time = min(60 * restart_count, 300)  # Max 5 minutes
                print(f"🔄 Restarting in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("❌ Max restart attempts reached. Stopping.")
                break

def main():
    """Main function"""
    try:
        # Setup signal handler untuk Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        
        # Check konfigurasi
        if not check_config():
            return
        
        # Show startup info
        show_startup_info()
        
        # Run bot
        asyncio.run(run_bot_with_restart())
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        print("Coba jalankan setup lagi: python setup_bot.py")

if __name__ == "__main__":
    main()