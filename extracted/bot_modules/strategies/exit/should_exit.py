"""Smart exit logic (simplified) using basic stop-loss and take-profit."""
from typing import Dict, List

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