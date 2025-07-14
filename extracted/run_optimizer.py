
import itertools
import json
from bot_modules.config.hybrid_loader import HybridConfig
from bot_modules.backtesting.data_loader import fetch_ohlcv
from bot_modules.backtesting.backtest_engine import backtest
from datetime import datetime

TOP_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def generate_param_grid(param_ranges):
    keys, values = zip(*param_ranges.items())
    return [dict(zip(keys, v)) for v in itertools.product(*values)]

def run_optimizer():
    base_config = HybridConfig().get_config()

    # Parameter yang ingin dioptimasi
    param_ranges = {
        "entry_threshold": [0.4, 0.5, 0.6],
        "exit_trailing": [0.8, 1.0, 1.2],
        "trailing_stop": [False, True]
    }

    param_grid = generate_param_grid(param_ranges)
    summary = {}

    print("🔍 Starting multi-symbol optimizer...")
    for symbol in TOP_SYMBOLS:
        print(f"🪙 Testing for {symbol}")
        data = fetch_ohlcv(symbol=symbol, interval="15m", limit=1000)

        best_result = None
        best_config = None

        for params in param_grid:
            test_config = base_config.copy()
            test_config.update(params)
            test_config["symbol"] = symbol

            result = backtest(test_config, data)
            print(f"  ✅ {params} -> PnL: {result['pnl']} | Winrate: {result['winrate']}")

            if not best_result or result["pnl"] > best_result["pnl"]:
                best_result = result
                best_config = params

        summary[symbol] = {
            "params": best_config,
            "result": best_result
        }

    # Simpan ke file
    with open("configs/best_live_config.json", "w") as f:
        json.dump(summary[TOP_SYMBOLS[0]], f, indent=2)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"best_configs_{now}.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n🏁 Optimization Finished!")
    for symbol, data in summary.items():
        print(f"🪙 {symbol}")
        print(f"   Params: {data['params']}")
        print(f"   Result: {data['result']}")
