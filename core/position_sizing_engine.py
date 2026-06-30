class PositionSizingEngine:
    def calculate_usdt_amount(self, balance, confidence, risk_score):
        if balance <= 0:
            return 0

        # Bakiyenin en fazla %10'u
        max_position = balance * 0.10

        if confidence >= 90:
            factor = 1.0
        elif confidence >= 80:
            factor = 0.75
        elif confidence >= 70:
            factor = 0.50
        else:
            factor = 0.30

        if risk_score < 40:
            factor *= 0.50

        amount = max_position * factor

        # Çok küçük emir açmasın
        if amount < 10:
            return 0

        return round(amount, 2)