#!/bin/bash

# Bot Trading Binance Futures - Installation Script
# Optimized untuk VPS 1GB RAM dengan Modal $5

echo "🤖 Bot Trading Binance Futures - Installer"
echo "==========================================="
echo "Optimized untuk VPS 1GB RAM dengan Modal $5"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: Running as root. Consider using a regular user for security."
fi

# Update system
echo "📦 Updating system packages..."
if command -v apt &> /dev/null; then
    sudo apt update && sudo apt upgrade -y
    PACKAGE_MANAGER="apt"
elif command -v yum &> /dev/null; then
    sudo yum update -y
    PACKAGE_MANAGER="yum"
elif command -v dnf &> /dev/null; then
    sudo dnf update -y
    PACKAGE_MANAGER="dnf"
else
    echo "❌ Unsupported package manager. Please install manually."
    exit 1
fi

# Install Python 3 and pip
echo "🐍 Installing Python 3 and pip..."
if [ "$PACKAGE_MANAGER" = "apt" ]; then
    sudo apt install -y python3 python3-pip python3-venv git curl wget unzip
elif [ "$PACKAGE_MANAGER" = "yum" ]; then
    sudo yum install -y python3 python3-pip git curl wget unzip
elif [ "$PACKAGE_MANAGER" = "dnf" ]; then
    sudo dnf install -y python3 python3-pip git curl wget unzip
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo "✅ Python $PYTHON_VERSION is compatible"
else
    echo "❌ Python $PYTHON_VERSION is too old. Required: $REQUIRED_VERSION+"
    exit 1
fi

# Create project directory
BOT_DIR="$HOME/bot-trading-futures"
echo "📁 Creating project directory: $BOT_DIR"
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

# Create virtual environment (recommended for VPS)
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing bot dependencies..."
if [ -f "requirements_optimized.txt" ]; then
    pip install -r requirements_optimized.txt
else
    # Install minimal dependencies if requirements file not found
    pip install python-binance==1.0.19 python-telegram-bot==20.7 aiohttp==3.9.1 psutil==5.9.6 python-dotenv==1.0.0
fi

# Create systemd service for auto-start
echo "🔧 Creating systemd service..."
SERVICE_FILE="/etc/systemd/system/bot-trading.service"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Bot Trading Binance Futures
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python $BOT_DIR/run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable bot-trading
echo "✅ Systemd service created and enabled"

# Create logs directory
mkdir -p logs

# Set up log rotation
echo "📄 Setting up log rotation..."
sudo tee /etc/logrotate.d/bot-trading > /dev/null <<EOF
$BOT_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    copytruncate
    maxsize 10M
}
EOF

# Create cron job for monitoring
echo "⏰ Setting up monitoring cron job..."
(crontab -l 2>/dev/null; echo "*/15 * * * * cd $BOT_DIR && ./venv/bin/python monitor_bot.py alerts >> logs/monitor.log 2>&1") | crontab -

# Create quick access commands
echo "🔗 Creating quick access commands..."
sudo tee /usr/local/bin/bot-trading > /dev/null <<EOF
#!/bin/bash
cd $BOT_DIR
source venv/bin/activate
exec ./start_bot.sh "\$@"
EOF

sudo chmod +x /usr/local/bin/bot-trading

# Create update script
tee update_bot.sh > /dev/null <<'EOF'
#!/bin/bash
echo "🔄 Updating Bot Trading..."
cd $(dirname "$0")
source venv/bin/activate

# Stop bot if running
sudo systemctl stop bot-trading

# Update dependencies
pip install --upgrade -r requirements_optimized.txt

# Restart bot
sudo systemctl start bot-trading

echo "✅ Bot updated and restarted"
EOF

chmod +x update_bot.sh

# Create backup script
tee backup_config.sh > /dev/null <<'EOF'
#!/bin/bash
echo "💾 Backing up bot configuration..."
cd $(dirname "$0")

BACKUP_DIR="$HOME/bot-backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bot_config_$TIMESTAMP.tar.gz"

tar -czf "$BACKUP_FILE" bot_config.json performance.json trades.json 2>/dev/null

echo "✅ Backup saved: $BACKUP_FILE"
EOF

chmod +x backup_config.sh

# Show system information
echo ""
echo "🖥️  System Information:"
echo "======================"
FREE_OUTPUT=$(free -h)
echo "💾 Memory:"
echo "$FREE_OUTPUT"
echo ""
echo "💽 Disk:"
df -h | head -n 2
echo ""
echo "🐍 Python: $(python3 --version)"

# Show installation summary
echo ""
echo "🎉 INSTALLATION COMPLETE!"
echo "========================="
echo ""
echo "📁 Bot installed in: $BOT_DIR"
echo "🔧 Virtual environment: $BOT_DIR/venv"
echo "⚙️  Systemd service: bot-trading"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Run setup: python setup_bot.py"
echo "2. Or use: bot-trading setup"
echo "3. Start bot: sudo systemctl start bot-trading"
echo "4. Check status: sudo systemctl status bot-trading"
echo "5. View logs: tail -f logs/bot.log"
echo ""
echo "🎮 QUICK COMMANDS:"
echo "• bot-trading start    - Start bot"
echo "• bot-trading stop     - Stop bot" 
echo "• bot-trading status   - Check status"
echo "• bot-trading logs     - View logs"
echo "• bot-trading monitor  - System monitor"
echo ""
echo "📱 TELEGRAM CONTROL:"
echo "• /start - Mulai bot"
echo "• /status - Status bot"
echo "• /balance - Cek saldo"
echo "• /testnet - Mode testnet"
echo "• /real - Mode real trading"
echo ""
echo "🔧 MAINTENANCE:"
echo "• ./update_bot.sh - Update bot"
echo "• ./backup_config.sh - Backup konfigurasi"
echo "• python monitor_bot.py - Performance monitor"
echo ""
echo "⚠️  IMPORTANT:"
echo "• Setup API keys dan Telegram bot dulu"
echo "• Test dengan testnet sebelum real trading"
echo "• Monitor bot secara berkala"
echo "• Backup konfigurasi secara berkala"
echo ""
echo "🚀 Ready untuk trading! Start dengan: python setup_bot.py"

# Deactivate virtual environment
deactivate