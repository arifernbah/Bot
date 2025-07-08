#!/usr/bin/env python3
"""
Monitor Script untuk Bot Trading Binance Futures
Script untuk monitoring performance dan resource usage
"""

import json
import os
import time
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

class BotMonitor:
    """Monitor untuk tracking performance bot"""
    
    def __init__(self):
        self.process = psutil.Process() if self.is_bot_running() else None
        self.performance_file = "performance.json"
        self.trades_file = "trades.json"
    
    def is_bot_running(self) -> bool:
        """Check apakah bot sedang running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # More specific pattern matching
                if any('bot_binance_futures.py' in arg for arg in proc.info['cmdline'] or []):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu = psutil.cpu_percent(interval=1)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_percent': memory.percent,
                'free_gb': round(memory.free / (1024**3), 2)
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_percent': round((disk.used / disk.total) * 100, 1)
            },
            'cpu_percent': cpu
        }
    
    def get_bot_process_stats(self) -> Dict[str, Any]:
        """Get bot process statistics"""
        if not self.process:
            return {}
        
        try:
            memory_info = self.process.memory_info()
            return {
                'pid': self.process.pid,
                'memory_mb': round(memory_info.rss / (1024**2), 2),
                'memory_percent': round(self.process.memory_percent(), 2),
                'cpu_percent': round(self.process.cpu_percent(), 2),
                'threads': self.process.num_threads(),
                'status': self.process.status(),
                'create_time': datetime.fromtimestamp(self.process.create_time()).isoformat()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
    
    def load_performance_data(self) -> Dict[str, Any]:
        """Load performance data dari file"""
        try:
            if os.path.exists(self.performance_file):
                with open(self.performance_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading performance data: {e}")
        
        return {
            'trades': [],
            'daily_stats': {},
            'system_stats': []
        }
    
    def save_performance_data(self, data: Dict[str, Any]):
        """Save performance data ke file"""
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving performance data: {e}")
    
    def load_trades_data(self) -> list:
        """Load trades data"""
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading trades data: {e}")
        
        return []
    
    def calculate_trading_stats(self, trades: list) -> Dict[str, Any]:
        """Calculate trading statistics"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'total_profit': 0,
                'max_profit': 0,
                'max_loss': 0,
                'profit_factor': 0
            }
        
        profits = [t.get('profit_pct', 0) for t in trades if 'profit_pct' in t]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]
        
        # Safer profit factor calculation
        losses_sum = sum(losses) if losses else 0
        if losses_sum != 0:
            profit_factor = abs(sum(wins) / losses_sum)
        else:
            profit_factor = float('inf') if wins else 0
        
        return {
            'total_trades': len(trades),
            'win_rate': (len(wins) / len(profits) * 100) if profits else 0,
            'avg_profit': sum(profits) / len(profits) if profits else 0,
            'total_profit': sum(profits),
            'max_profit': max(profits) if profits else 0,
            'max_loss': min(profits) if profits else 0,
            'profit_factor': profit_factor,
            'total_wins': len(wins),
            'total_losses': len(losses)
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive monitoring report"""
        # System stats
        system_stats = self.get_system_stats()
        
        # Bot process stats
        bot_stats = self.get_bot_process_stats()
        
        # Performance data
        performance_data = self.load_performance_data()
        trades_data = self.load_trades_data()
        trading_stats = self.calculate_trading_stats(trades_data)
        
        # Generate report
        report = f"""
🤖 BOT TRADING MONITORING REPORT
{'='*50}
⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 SYSTEM RESOURCES:
💾 RAM: {system_stats['memory']['used_percent']:.1f}% used 
    Total: {system_stats['memory']['total_gb']}GB
    Available: {system_stats['memory']['available_gb']}GB
    
💽 Disk: {system_stats['disk']['used_percent']:.1f}% used
    Free: {system_stats['disk']['free_gb']}GB
    
🖥️  CPU: {system_stats['cpu_percent']:.1f}%

🤖 BOT PROCESS:
"""
        
        if bot_stats:
            report += f"""✅ Status: Running (PID: {bot_stats['pid']})
🧠 Memory: {bot_stats['memory_mb']}MB ({bot_stats['memory_percent']:.1f}%)
⚡ CPU: {bot_stats['cpu_percent']:.1f}%
🧵 Threads: {bot_stats['threads']}
⏰ Started: {bot_stats['create_time'][:19]}
"""
        else:
            report += "❌ Bot tidak berjalan\n"
        
        report += f"""
📈 TRADING PERFORMANCE:
💰 Total Trades: {trading_stats['total_trades']}
🎯 Win Rate: {trading_stats['win_rate']:.1f}%
💵 Avg Profit: {trading_stats['avg_profit']:.2%}
📊 Total P&L: {trading_stats['total_profit']:.2%}
📈 Max Profit: {trading_stats['max_profit']:.2%}
📉 Max Loss: {trading_stats['max_loss']:.2%}
⚖️  Profit Factor: {trading_stats['profit_factor']:.2f}

🏆 WINS/LOSSES:
✅ Wins: {trading_stats['total_wins']}
❌ Losses: {trading_stats['total_losses']}

{'='*50}
"""
        
        return report
    
    def check_alerts(self) -> list:
        """Check untuk alerts/warnings"""
        alerts = []
        
        # System resource alerts
        system_stats = self.get_system_stats()
        
        if system_stats['memory']['used_percent'] > 85:
            alerts.append(f"⚠️  HIGH MEMORY USAGE: {system_stats['memory']['used_percent']:.1f}%")
        
        if system_stats['disk']['used_percent'] > 90:
            alerts.append(f"⚠️  LOW DISK SPACE: {system_stats['disk']['free_gb']:.1f}GB free")
        
        if system_stats['cpu_percent'] > 80:
            alerts.append(f"⚠️  HIGH CPU USAGE: {system_stats['cpu_percent']:.1f}%")
        
        # Bot process alerts - adjust memory threshold for 1GB VPS
        if bot_stats and bot_stats['memory_mb'] > 150:  # Lowered from 200MB
            alerts.append(f"⚠️  BOT HIGH MEMORY: {bot_stats['memory_mb']}MB")
        
        # Bot not running alert
        if not self.is_bot_running():
            alerts.append("🚨 BOT NOT RUNNING!")
        
        return alerts
    
    def log_system_stats(self):
        """Log system stats ke performance file"""
        performance_data = self.load_performance_data()
        system_stats = self.get_system_stats()
        bot_stats = self.get_bot_process_stats()
        
        # Add timestamp and bot stats to system stats
        system_stats['bot_stats'] = bot_stats
        
        # Keep only last 100 system stat entries untuk menghemat space
        if 'system_stats' not in performance_data:
            performance_data['system_stats'] = []
        
        performance_data['system_stats'].append(system_stats)
        
        if len(performance_data['system_stats']) > 100:
            performance_data['system_stats'] = performance_data['system_stats'][-100:]
        
        self.save_performance_data(performance_data)

def print_status():
    """Print current status"""
    monitor = BotMonitor()
    
    print("🔍 Bot Trading Monitor")
    print("=" * 30)
    
    # Check alerts first
    alerts = monitor.check_alerts()
    if alerts:
        print("🚨 ALERTS:")
        for alert in alerts:
            print(f"   {alert}")
        print()
    
    # Generate and print report
    report = monitor.generate_report()
    print(report)
    
    # Log stats
    monitor.log_system_stats()

def continuous_monitor(interval_minutes: int = 5):
    """Run continuous monitoring"""
    print(f"🔄 Starting continuous monitoring (every {interval_minutes} minutes)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            print_status()
            print(f"\n⏰ Next check in {interval_minutes} minutes...")
            print("-" * 50)
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            continuous_monitor(interval)
        elif sys.argv[1] == "alerts":
            monitor = BotMonitor()
            alerts = monitor.check_alerts()
            if alerts:
                for alert in alerts:
                    print(alert)
            else:
                print("✅ No alerts")
        else:
            print("Usage:")
            print("  python monitor_bot.py                 # Single status check")
            print("  python monitor_bot.py continuous [minutes]  # Continuous monitoring")
            print("  python monitor_bot.py alerts          # Check alerts only")
    else:
        print_status()

if __name__ == "__main__":
    main()