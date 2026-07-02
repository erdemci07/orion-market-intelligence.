class RiskEngine:
    def calculate_risk_score(self, regime):
        name = regime["regime"]

        if name == "AGGRESSIVE":
            return 95

        if name == "BULLISH":
            return 85

        if name == "NORMAL":
            return 70

        if name == "CAREFUL":
            return 55

        if name == "DEFENSIVE":
            return 40

        if name == "SURVIVAL":
            return 25

        return 50