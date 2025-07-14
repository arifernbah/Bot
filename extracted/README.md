# Binance Futures Modular Trading Bot (Self-Adaptive, Auto Symbol, News Sentiment)

Bot trading 24/7 untuk Binance Futures yang dirancang modular, otomatis, dan adaptif terhadap kondisi pasar.
Mendukung auto-symbol, risk management dinamis, serta integrasi sentimen berita & analisis data historis.

---

## 📦 Fitur Utama
- ✅ Auto Symbol Loader (berbasis volume tertinggi)
- ✅ Risk Management Otomatis (Kelly, fixed, atau hybrid)
- ✅ News Sentiment Analysis (via NewsAPI)
- ✅ Strategi Entry & Exit Modular
- ✅ 24/7 Trading Loop
- ✅ Konfigurasi Full via JSON
- ✅ Telegram Notifikasi (opsional)
- ✅ Logging ke CSV untuk analisa performa
- ✅ Integrasi `pandas` untuk indikator dan analitik

---

## 📁 Struktur Folder
```
main.py                          ← Entry point bot
config_hybrid_all.json           ← Konfigurasi parameter
.env                             ← API keys

📁 bot_modules/
├── analysis/                    ← Analisa pasar teknikal (pakai pandas)
├── sentiment/                  ← Sentimen berita (NewsAPI)
├── strategies/                 ← Entry & exit logic
├── feedback/                   ← Evaluasi performa & logging CSV
├── exchange/                   ← Handler order Binance
├── filters/, risk/, utils/     ← Risk control, pair loader
├── monitoring/                 ← Pemantau modal & pencatatan log trade
├── telegram/                   ← Telegram handler
├── logs/                       ← Hasil log trade & equity (.csv)
```

---

## ⚙️ Cara Setup

### 1. Siapkan `.env`
```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token (optional)
TELEGRAM_CHAT_ID=your_chat_id (optional)
NEWS_API_KEY=your_news_api_key
```

### 2. Edit Konfigurasi JSON
File: `config_hybrid_all.json`
```json
{
  "entry": {
    "min_score_threshold": 0.7,
    "max_active_trades": 3
  },
  "risk": {
    "use_kelly": true,
    "risk_multiplier": 1.0
  },
  "exit": {
    "use_trailing_stop": true,
    "take_profit_ratio": 1.5
  }
}
```

---

## ▶️ Menjalankan Bot
```bash
python main.py
```

---

## 🔁 Sistem Kerja
- Load auto top symbols → deteksi peluang entry
- Scoring berdasarkan analisa teknikal (pandas)
- Cek sentimen berita → tambahkan multiplier entry
- Hitung posisi via risk system → eksekusi order
- Exit dinamis berdasarkan kondisi (profit, pattern, trailing)
- Log disimpan ke file CSV
- Loop 24/7

---

## 📊 Komponen Utama
| Komponen          | Penjelasan Singkat                                        |
|------------------|------------------------------------------------------------|
| Entry Logic      | Scoring, confluence, liquidity, pattern, volume (pandas)  |
| Exit Logic       | Momentum, emergency, trailing, structure-based            |
| Risk Sizing      | Kelly Criterion atau fixed (hybrid)                       |
| Sentiment        | Analisis berita real-time via NewsAPI                     |
| Symbol Loader    | Ambil top-pair otomatis (by volume USDT)                  |
| Telegram         | Notifikasi live trade (optional)                          |
| Monitoring       | Simpan log ke CSV untuk evaluasi performa                 |

---

## 🧠 Optimal Digunakan Untuk
- Modal mulai $50 hingga $1000+
- Cocok untuk bot VPS ringan (1GB RAM)
- Tidak butuh interaksi manual setelah setup

---

## 📌 Catatan Tambahan
- Default adalah live trading mode
- Untuk test: gunakan akun Binance testnet dan ganti API Key
- Mudah menambahkan strategi baru karena strukturnya modular
- Logging CSV bisa dibuka di Excel/Google Sheets

---

## 📥 Rekomendasi API Gratis
| API            | Fungsi                 | Limitasi Gratis         |
|----------------|------------------------|--------------------------|
| Binance API    | Data dan order         | Cukup untuk bot ringan   |
| NewsAPI.org    | Sentimen berita        | 100 requests per hari    |
| Telegram Bot   | Notifikasi             | Gratis selamanya         |