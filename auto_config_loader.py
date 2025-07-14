
import json
from binance.client import Client
from binance.exceptions import BinanceAPIException
from config.equity_enhanced_config import EnhancedEquityTrading

def get_futures_balance(api_key, api_secret):
    """Get USDT balance from Binance Futures account with proper error handling"""
    try:
        # Deteksi testnet atau real dengan lebih akurat
        is_testnet = False
        if api_key and api_secret:
            # Hanya set testnet jika API key mengandung 'test' (explicit testnet)
            if "test" in api_key.lower() or "testnet" in api_key.lower():
                is_testnet = True
        
        client = Client(api_key, api_secret, testnet=is_testnet)
        
        # Test koneksi dulu
        client.futures_ping()
        
        # Ambil balance dari Futures account
        balances = client.futures_account_balance()
        usdt_balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
        
        print(f"[INFO] Successfully connected to Binance Futures ({'TESTNET' if is_testnet else 'REAL'})")
        return usdt_balance
        
    except BinanceAPIException as e:
        print(f"[ERROR] Binance API Error: {e}")
        if "API-key format invalid" in str(e):
            print("[ERROR] API key format salah atau tidak valid")
        elif "restricted location" in str(e):
            print("[ERROR] Server Anda diblokir oleh Binance. Gunakan VPS di region yang didukung.")
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to get Futures balance: {e}")
        return 0

def load_config_auto(api_key, api_secret, config_file="config_hybrid_all.json"):
    """Load configuration based on account balance with enhanced equity system"""
    if not api_key or not api_secret:
        print("[ERROR] API key atau secret tidak tersedia")
        return None
    
    balance = get_futures_balance(api_key, api_secret)
    
    if balance == 0:
        print("[WARN] Tidak bisa mendapatkan balance. Menggunakan config default.")
        balance = 3.0  # Default minimal balance
    
    print(f"[INFO] Detected Futures Balance: ${balance:.2f}")
    
    # Determine testnet / real mode for downstream components
    is_testnet = False
    if api_key:
        is_testnet = ("testnet" in api_key.lower()) or (len(api_key) < 50)

    # Initialize enhanced equity trading system
    try:
        equity_trader = EnhancedEquityTrading(balance)
        print(f"[EQUITY] Enhanced equity system initialized")
        print(f"[EQUITY] Risk Level: {equity_trader.risk_level}")
        print(f"[EQUITY] Base Risk: {equity_trader.base_risk_percent}%")
        print(f"[EQUITY] Max Drawdown: {equity_trader.max_drawdown_percent}%")
        
        # Get trading parameters from equity system
        config = equity_trader.get_trading_parameters()
        
        # Add essential parameters
        config['initial_balance'] = balance
        config['api_key'] = api_key
        config['api_secret'] = api_secret
        config['is_testnet'] = is_testnet  # <-- ensure downstream attribute exists
        
        # Add equity trader instance to config
        config['equity_trader'] = equity_trader
        
        # Add equity-specific configurations
        config['equity_trading'] = {
            'enabled': True,
            'base_risk_percent': equity_trader.base_risk_percent,
            'max_risk_percent': equity_trader.max_risk_percent,
            'max_drawdown_percent': equity_trader.max_drawdown_percent,
            'daily_loss_limit': equity_trader.daily_loss_limit,
            'daily_profit_target': equity_trader.daily_profit_target
        }
        
        print(f"[SUCCESS] Config loaded with enhanced equity system")
        return config
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize equity system: {e}")
        # Fallback to original hybrid config
        with open(config_file, "r") as f:
            all_configs = json.load(f)

        keys = sorted([int(k.strip('$')) for k in all_configs])
        eligible_keys = [k for k in keys if k <= balance]

        if not eligible_keys:
            chosen_key = keys[0]
            print(f"[WARN] Balance ${balance:.2f} terlalu kecil. Menggunakan config minimal ${chosen_key}")
        else:
            chosen_key = max(eligible_keys)

        print(f"[INFO] Using fallback config for balance: ${chosen_key}")
        config = all_configs[f"${chosen_key}"]
        config['initial_balance'] = balance
        config['api_key'] = api_key
        config['api_secret'] = api_secret
        config['is_testnet'] = is_testnet
        return config
