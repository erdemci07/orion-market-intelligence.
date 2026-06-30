class RiskEngine:
    def calculate_risk_score(self, regime):
        if regime["regime"] == "BULLISH":
            return 85

        if regime["regime"] == "NEUTRAL":
            return 65

        if regime["regime"] == "RISKY":
            return 40

        if regime["regime"] == "PANIC":
            return 20

        return 50