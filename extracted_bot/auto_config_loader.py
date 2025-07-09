
import json
from binance.client import Client

def get_futures_balance(api_key, api_secret):
    client = Client(api_key, api_secret)
    balances = client.futures_account_balance()
    usdt_balance = next((float(x['balance']) for x in balances if x['asset'] == 'USDT'), 0)
    return usdt_balance

def load_config_auto(api_key, api_secret, config_file="config_hybrid_all.json"):
    balance = get_futures_balance(api_key, api_secret)
    print(f"[INFO] Detected Futures Balance: ${balance:.2f}")

    with open(config_file, "r") as f:
        all_configs = json.load(f)

    keys = sorted([int(k.strip('$')) for k in all_configs])
    eligible_keys = [k for k in keys if k <= balance]

    if not eligible_keys:
        chosen_key = keys[0]
    else:
        chosen_key = max(eligible_keys)

    print(f"[INFO] Using config for balance: ${chosen_key}")
    return all_configs[f"${chosen_key}"]
