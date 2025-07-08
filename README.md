# ARIFBOT PRO – Refactored (July 2025)

**Level**: Pro Trader 4  
**Language**: Python 3.10+

## 🗂 Folder Layout

```
ARIFBOT_PRO/
├─ core/                  # Bot runner & execution engine
│   └─ bot_runner.py
├─ modules/               # All analytical and helper modules
│   ├─ indicators.py
│   ├─ market_analysis.py
│   ├─ position_sizing.py
│   ├─ risk_manager.py
│   ├─ session_timing.py
│   ├─ telegram_handler.py
│   ├─ smart_trading.py
│   └─ strategies/        # <<< new – place extra strategies here
├─ config/                # (optional) future config helpers
├─ logs/                  # runtime logs
├─ reports/               # PnL / metrics exports
├─ bot_binance_futures.py # backward‑compat alias → core.bot_runner
├─ run_bot.py             # entry point
├─ requirements_pro_trader.txt
└─ README.md              # this file
```

## 🚀 Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements_pro_trader.txt

export BINANCE_API_KEY=xxx
export BINANCE_SECRET=xxx
export TELEGRAM_TOKEN=xxx
export TELEGRAM_CHAT_ID=123456789
# Uncomment for testnet
# export BINANCE_USE_TESTNET=true

python run_bot.py
```

## 🔧 Extending

* **Add Strategies** – drop a new module into `modules/strategies/`
  and import it in `modules/strategies/__init__.py`.
* **Config Helpers** – place reusable config logic inside `config/`.
* **Logs & Reports** – bot writes runtime logs to `logs/`; you can
  save PnL or analytics to `reports/` for later analysis.

---

_Refactor performed automatically on 2025-07-08 00:44 UTC_
