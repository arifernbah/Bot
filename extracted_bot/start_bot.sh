#!/bin/bash

# Start Bot Trading Binance Futures
# Script untuk menjalankan bot di VPS dengan mudah

echo "🤖 Bot Trading Binance Futures Starter"
echo "======================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 tidak ditemukan!"
    echo "Install dengan: sudo apt install python3 python3-pip"
    exit 1
fi

# Check if config exists
if [ ! -f "bot_config.json" ]; then
    echo "❌ Konfigurasi tidak ditemukan!"
    echo "Jalankan setup dulu: python3 setup_bot.py"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import binance, telegram" &> /dev/null; then
    echo "⚠️  Dependencies belum terinstall"
    echo "📦 Installing dependencies..."
    pip3 install -r requirements_optimized.txt
fi

# Function to start bot
start_bot() {
    echo "🚀 Starting bot..."
    
    # Create logs directory if not exists
    mkdir -p logs
    
    # Start bot in background with nohup
    nohup python3 run_bot.py > logs/bot.log 2>&1 &
    
    # Get PID
    BOT_PID=$!
    echo $BOT_PID > bot.pid
    
    echo "✅ Bot started with PID: $BOT_PID"
    echo "📄 Logs: logs/bot.log"
    echo "📱 Control via Telegram commands"
    
    # Show initial logs
    echo ""
    echo "📊 Initial output:"
    sleep 2
    tail -n 10 logs/bot.log
}

# Function to stop bot
stop_bot() {
    if [ -f "bot.pid" ]; then
        BOT_PID=$(cat bot.pid)
        if ps -p $BOT_PID > /dev/null; then
            echo "🛑 Stopping bot (PID: $BOT_PID)..."
            kill $BOT_PID
            rm bot.pid
            echo "✅ Bot stopped"
        else
            echo "❌ Bot tidak berjalan"
            rm bot.pid
        fi
    else
        echo "❌ Bot PID file tidak ditemukan"
        # Try to find and kill bot process
        BOT_PID=$(pgrep -f "bot_binance_futures.py")
        if [ ! -z "$BOT_PID" ]; then
            echo "🔍 Found bot process: $BOT_PID"
            kill $BOT_PID
            echo "✅ Bot stopped"
        fi
    fi
}

# Function to check bot status
check_status() {
    echo "🔍 Checking bot status..."
    
    if [ -f "bot.pid" ]; then
        BOT_PID=$(cat bot.pid)
        if ps -p $BOT_PID > /dev/null; then
            echo "✅ Bot running (PID: $BOT_PID)"
            
            # Show memory usage
            MEM_USAGE=$(ps -p $BOT_PID -o %mem --no-headers)
            echo "🧠 Memory usage: ${MEM_USAGE}%"
            
            # Show last few log lines
            if [ -f "logs/bot.log" ]; then
                echo ""
                echo "📄 Recent logs:"
                tail -n 5 logs/bot.log
            fi
        else
            echo "❌ Bot tidak berjalan (PID file ada tapi process mati)"
            rm bot.pid
        fi
    else
        BOT_PID=$(pgrep -f "bot_binance_futures.py")
        if [ ! -z "$BOT_PID" ]; then
            echo "⚠️  Bot berjalan tapi tidak ada PID file"
            echo "PID: $BOT_PID"
            echo $BOT_PID > bot.pid
        else
            echo "❌ Bot tidak berjalan"
        fi
    fi
}

# Function to view logs
view_logs() {
    if [ -f "logs/bot.log" ]; then
        echo "📄 Bot logs (press 'q' to quit):"
        tail -f logs/bot.log
    else
        echo "❌ Log file tidak ditemukan"
    fi
}

# Function to restart bot
restart_bot() {
    echo "🔄 Restarting bot..."
    stop_bot
    sleep 2
    start_bot
}

# Function to show system info
system_info() {
    echo "🖥️  System Information:"
    echo "====================="
    
    # Memory info
    FREE_OUTPUT=$(free -h)
    echo "💾 Memory:"
    echo "$FREE_OUTPUT"
    
    # Disk info
    echo ""
    echo "💽 Disk:"
    df -h | grep -E "(Filesystem|/dev/)"
    
    # CPU info
    echo ""
    echo "🖥️  CPU:"
    echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
    
    # Python version
    echo ""
    echo "🐍 Python: $(python3 --version)"
}

# Main menu
show_menu() {
    echo ""
    echo "Pilih opsi:"
    echo "1. Start bot"
    echo "2. Stop bot"
    echo "3. Restart bot"
    echo "4. Check status"
    echo "5. View logs"
    echo "6. System info"
    echo "7. Monitor bot"
    echo "8. Setup bot"
    echo "9. Exit"
    echo ""
}

# Handle command line arguments
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    info)
        system_info
        ;;
    monitor)
        if [ -f "monitor_bot.py" ]; then
            python3 monitor_bot.py
        else
            echo "❌ monitor_bot.py tidak ditemukan"
        fi
        ;;
    setup)
        python3 setup_bot.py
        ;;
    *)
        # Interactive mode
        while true; do
            show_menu
            read -p "Pilih (1-9): " choice
            
            case $choice in
                1) start_bot ;;
                2) stop_bot ;;
                3) restart_bot ;;
                4) check_status ;;
                5) view_logs ;;
                6) system_info ;;
                7) 
                    if [ -f "monitor_bot.py" ]; then
                        python3 monitor_bot.py
                    else
                        echo "❌ monitor_bot.py tidak ditemukan"
                    fi
                    ;;
                8) python3 setup_bot.py ;;
                9) 
                    echo "👋 Goodbye!"
                    exit 0
                    ;;
                *)
                    echo "❌ Pilihan tidak valid"
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
        done
        ;;
esac