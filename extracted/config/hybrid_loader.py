
import json
from config.equity_enhanced_config import EnhancedEquityTrading

class HybridConfig:
    def __init__(self, json_path="config/config_hybrid_all.json", balance=10.0):
        with open(json_path, "r") as f:
            self.raw_config = json.load(f)
        self.enhanced = EnhancedEquityTrading(balance)
        self._merge_dynamic_logic()

        # Dekompresi modular
        self.entry = self.raw_config.get("entry", {})
        self.exit = self.raw_config.get("exit", {})
        self.risk = self.raw_config.get("risk", {})
        self.telegram = self.raw_config.get("telegram", {})

    def _merge_dynamic_logic(self):
        self.raw_config["kelly_position_size"] = self.enhanced.kelly_position_size
        self.raw_config["current_drawdown"] = self.enhanced.current_drawdown
        self.raw_config["confidence_threshold"] = self.enhanced.get_confidence_threshold()
        self.raw_config["portfolio_heat"] = self.enhanced.portfolio_heat

    def get_config(self):
        return self.raw_config
