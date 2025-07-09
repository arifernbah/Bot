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

## 🚀 Quick Start -> ## 🚀 Deployment Guide

### 1  Create & activate virtual env
```bash
python3 -m venv venv && source venv/bin/activate
```

### 2  Install dependencies
Choose the full professional stack:
```bash
pip install -r requirements_pro_trader.txt
```
_(or use `requirements.txt` for the minimal build)_

### 3  Provide credentials
Copy the example file and fill it with your keys:
```bash
cp .env.example .env
```
Then edit `.env` or export the variables manually:
```bash
export API_KEY=YOUR_BINANCE_KEY
export API_SECRET=YOUR_BINANCE_SECRET
export TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
export TELEGRAM_CHAT_ID=123456789
```
To run exclusively on testnet add:
```bash
export BINANCE_USE_TESTNET=true
```

### 4  Run the bot
• Dynamic single-run (auto config & Kelly sizing):
```bash
python3 main.py
```
• Long-running service with auto-restart & monitoring:
```bash
python3 run_bot.py
```

### 5  Server requirements
* 1 GB RAM (Swap recommended)
* Python 3.10+
* Outbound HTTPS (443) access
* Ports **NOT** required to be open – all communication is outbound.

---
The bot now pulls real-time price data from Binance Futures for its safety check (see `main.py -> fetch_recent_prices`); no dummy datasets remain.

## 🔧 Extending

* **Add Strategies** – drop a new module into `modules/strategies/`
  and import it in `modules/strategies/__init__.py`.
* **Config Helpers** – place reusable config logic inside `config/`.
* **Logs & Reports** – bot writes runtime logs to `logs/`; you can
  save PnL or analytics to `reports/` for later analysis.

---

_Refactor performed automatically on 2025-07-08 00:44 UTC_
