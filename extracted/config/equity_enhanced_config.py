class EnhancedEquityTrading:
    def __init__(self, balance):
        self.balance = balance
        self.initial_equity = balance
        self.current_drawdown = 0
        self.peak_equity = balance
        self.kelly_multiplier = 0.02
        self.portfolio_heat = 0.0

        self.trades_history = []
        self.pnl_log = []

        self.kelly_position_size = self.calculate_kelly_position()

    def update_equity(self, new_equity):
        if new_equity > self.peak_equity:
            self.peak_equity = new_equity
        drawdown = ((self.peak_equity - new_equity) / self.peak_equity) * 100
        self.current_drawdown = round(drawdown, 2)

        self.kelly_position_size = self.calculate_kelly_position()

    def calculate_kelly_position(self):
        return round(self.balance * self.kelly_multiplier, 2)

    def get_confidence_threshold(self):
        if self.current_drawdown > 15:
            return 0.9
        elif self.current_drawdown > 10:
            return 0.8
        return 0.7
