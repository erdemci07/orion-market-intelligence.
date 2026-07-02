class PositionSizingEngine:
    def calculate_usdt_amount(self, balance, confidence, risk_score, regime_name):
        if balance <= 0:
            return 0

        max_percent_by_regime = {
            "AGGRESSIVE": 0.15,
            "BULLISH": 0.10,
            "NORMAL": 0.07,
            "CAREFUL": 0.05,
            "DEFENSIVE": 0.03,
            "SURVIVAL": 0.01,
        }

        max_percent = max_percent_by_regime.get(regime_name, 0.03)
        max_position = balance * max_percent

        if confidence >= 90:
            factor = 1.0
        elif confidence >= 80:
            factor = 0.75
        elif confidence >= 70:
            factor = 0.50
        else:
            factor = 0.30

        if risk_score < 40:
            factor *= 0.60

        amount = max_position * factor

        if amount < 10:
            return 0

        return round(amount, 2)