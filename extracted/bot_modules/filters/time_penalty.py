# ⏱️ Waktu sebagai penalty faktor (bukan filter keras)
from datetime import datetime

def get_time_penalty():
    """
    Beri penalti pada skor entry jika waktu saat ini di luar jam aktif (Asia dini hari atau pre-market).
    """
    hour = datetime.utcnow().hour
    if 0 <= hour <= 6 or hour >= 23:
        return -1
    return 0
