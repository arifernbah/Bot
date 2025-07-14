# 📘 DEVELOPER GUIDE / PANDUAN PENGEMBANG

> Bahasa: 🇮🇩 Bahasa Indonesia / 🇬🇧 English  
> Last updated: [akan diperbarui manual saat release]

---

## 🇮🇩 PANDUAN BAHASA INDONESIA

### 📌 Struktur Folder Utama
- `main.py` → Titik masuk utama bot.
- `bot_modules/` → Semua logika trading modular.
- `configs/` dan `data/` → Konfigurasi & memori strategi.
- `.env` → Kunci API dan setelan sensitif.

### 🔁 Alur Bot
1. Mulai dari `main.py`
2. Load config & symbol
3. Analisis strategi entry/exit
4. Kirim order melalui `order_handler`
5. Simpan feedback & update equity

### ⚙️ Modul Penting
- `trade_executor.py` → Logika eksekusi sinyal.
- `order_handler.py` → API ke Binance.
- `risk/` → Mode fixed dan Kelly.
- `telegram/` → Listener command Telegram.
- `feedback/` → Pembelajaran strategi.

---

## 🇬🇧 ENGLISH GUIDE

### 📌 Main Folder Structure
- `main.py` → Main entry point.
- `bot_modules/` → All trading logic modules.
- `configs/`, `data/` → Configs and strategy memory.
- `.env` → API keys and sensitive settings.

### 🔁 Bot Execution Flow
1. Starts from `main.py`
2. Loads configuration & active symbols
3. Processes entry/exit logic
4. Executes via `order_handler`
5. Saves feedback & updates equity tracking

### ⚙️ Key Modules
- `trade_executor.py` → Signal execution logic
- `order_handler.py` → Communicates with Binance
- `risk/` → Fixed & Kelly modes
- `telegram/` → Telegram command listener
- `feedback/` → Strategy adaptation

---

📎 Tips:
- Konfigurasi utama berada di `config_hybrid_all.json` (editable)
- Gunakan `equity_tracker.py` untuk memantau performa modal
- Semua dependensi ada di `requirements.txt`