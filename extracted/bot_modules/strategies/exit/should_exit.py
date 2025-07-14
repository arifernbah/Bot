"""Smart exit logic (simplified) using basic stop-loss and take-profit."""
from typing import Dict, List
from bot_modules.ict.liquidity import detect_liquidity_zones
from bot_modules.ict.market_structure import analyze_structure
from bot_modules.ict.order_blocks import detect_order_blocks
from bot_modules.ict.fvg import detect_fvg

class SmartExit:
    def __init__(self, config):
        self.config = config

    # ------------------------------------------------------------------
    def should_exit(
        self,
        position: Dict,
        current_price: float,
        klines_data: List[List] | None = None,
        entry_analysis: Dict | None = None,
    ) -> Dict:
        entry_price = float(position.get("entryPrice", 0))
        if not entry_price:
            return {"action": "hold", "reason": "no_entry_price"}
        side = "long" if float(position.get("positionAmt", 0)) > 0 else "short"

        # Calc PnL
        pnl_pct = (
            (current_price - entry_price) / entry_price
            if side == "long"
            else (entry_price - current_price) / entry_price
        )

        # ICT-based early exit: liquidity sweep detection
        if klines_data and len(klines_data) >= 50:
            closes = [float(k[4]) for k in klines_data]
            liq = detect_liquidity_zones(closes)
            struct = analyze_structure(closes)
            opens = [float(k[1]) for k in klines_data]
            highs = [float(k[2]) for k in klines_data]
            lows = [float(k[3]) for k in klines_data]
            ob = detect_order_blocks(opens, closes)
            fvg = detect_fvg(highs, lows)

            # Exit if liquidity sweep against position bias
            if side == "long" and liq["bias"] == "bearish" and liq["equal_high_count"] >= 3:
                return {"action": "close", "reason": "liquidity_sweep_up", "urgency": "HIGH"}
            if side == "short" and liq["bias"] == "bullish" and liq["equal_low_count"] >= 3:
                return {"action": "close", "reason": "liquidity_sweep_down", "urgency": "HIGH"}

            # Exit on strong opposite Order Block or FVG
            if side == "long" and (ob["bearish_ob"] >= 1 or fvg["bearish_fvg"] >= 1):
                return {"action": "close", "reason": "bearish_ob_fvg", "urgency": "MEDIUM"}
            if side == "short" and (ob["bullish_ob"] >= 1 or fvg["bullish_fvg"] >= 1):
                return {"action": "close", "reason": "bullish_ob_fvg", "urgency": "MEDIUM"}

            # Exit on market structure shift
            if side == "long" and struct["bias"] == "bearish":
                return {"action": "close", "reason": "structure_shift_bearish", "urgency": "MEDIUM"}
            if side == "short" and struct["bias"] == "bullish":
                return {"action": "close", "reason": "structure_shift_bullish", "urgency": "MEDIUM"}

        # Basic SL / TP thresholds from config else defaults
        tp = getattr(self.config, "tp_percent", 1.0) / 100
        sl = getattr(self.config, "sl_percent", 3.0) / 100

        if pnl_pct >= tp:
            return {
                "action": "close",
                "reason": f"take_profit {pnl_pct:.2%}",
                "urgency": "LOW",
            }
        if pnl_pct <= -sl:
            return {
                "action": "close",
                "reason": f"stop_loss {pnl_pct:.2%}",
                "urgency": "HIGH",
            }
        return {"action": "hold", "reason": "within_range", "urgency": "NONE"}