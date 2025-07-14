# 🎯 Entry Scoring System


# ⏱️ Integrasi time_penalty
from bot_modules.filters.time_penalty import get_time_penalty
from bot_modules.feedback.entry_feedback import get_strategy_confidence
from bot_modules.analysis.market_tf_filter import analyze_higher_tf
from bot_modules.analysis.market_context import detect_market_context
from bot_modules.strategies.entry.trend_strength import classify_trend_strength, calculate_trend_strength


def calculate_entry_score(signals: dict, prices: list = None, higher_prices: list = None) -> int:
    def conflicting_signals(signals):
        return (signals.get('rsi') == 'bearish' and signals.get('structure') == 'breakout')
            or (signals.get('rsi') == 'bullish' and signals.get('structure') == 'breakdown')
    """
    Hitung skor confidence entry berdasarkan sinyal yang tersedia.
    signals: dictionary seperti
    {
        "rsi": "bullish",
        "structure": "breakout",
        "sentiment": "bullish",
        "is_volatile": True,
    }
    """
    score = 0

    # Cek higher timeframe trend
    if higher_prices:
        htf_trend = analyze_higher_tf(higher_prices)
        if htf_trend == "bullish" and signals.get("rsi") == "bearish":
            return -1
        if htf_trend == "bearish" and signals.get("rsi") == "bullish":
            return -1
    
    # Delay entry jika sinyal bertentangan
    if conflicting_signals(signals):
        return -1  # sinyal konflik, hindari entry

    # Dynamic confidence weighting
    score += get_strategy_confidence
from bot_modules.analysis.market_tf_filter import analyze_higher_tf("rsi_signal") * (1 if signals.get("rsi") == "bullish" else 0)
    score += get_strategy_confidence
from bot_modules.analysis.market_tf_filter import analyze_higher_tf("structure_breakout") * (1 if signals.get("structure") == "breakout" else 0)
    
    if signals.get("rsi") == "bullish":
        score += 1
    if signals.get("structure") in ["breakout", "strong_trend"]:
        score += 1
    if signals.get("sentiment") == "bullish":
        score += 1
    if signals.get("is_volatile"):
        score += 1
    
    # Deteksi konteks market
    context = detect_market_context(prices)

    # +1 jika tren kuat dan searah

    if prices:
        slope = calculate_trend_strength(prices)
        trend_type = classify_trend_strength(slope)
        if trend_type in ["strong_up", "strong_down"]:
            score += 1

    # Koreksi skor berdasarkan waktu (jam rawan dikurangi 1)
    score += get_time_penalty
from bot_modules.feedback.entry_feedback import get_strategy_confidence
from bot_modules.analysis.market_tf_filter import analyze_higher_tf
from bot_modules.analysis.market_context import detect_market_context
from bot_modules.strategies.entry.trend_strength import classify_trend_strength, calculate_trend_strength()

    return score

def is_confident_entry(score: int, threshold: int = 3) -> bool:
    """
    Menentukan apakah skor cukup tinggi untuk entry.
    """
    
    # Deteksi konteks market
    context = detect_market_context(prices)

    # +1 jika tren kuat dan searah

    if prices:
        slope = calculate_trend_strength(prices)
        trend_type = classify_trend_strength(slope)
        if trend_type in ["strong_up", "strong_down"]:
            score += 1

    # Koreksi skor berdasarkan waktu (jam rawan dikurangi 1)
    score += get_time_penalty
from bot_modules.feedback.entry_feedback import get_strategy_confidence
from bot_modules.analysis.market_tf_filter import analyze_higher_tf
from bot_modules.analysis.market_context import detect_market_context
from bot_modules.strategies.entry.trend_strength import classify_trend_strength, calculate_trend_strength()

    return score >= threshold
