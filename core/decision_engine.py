class DecisionEngine:
    def decide(self, confidence, regime):
        if regime == "PANIC":
            if confidence >= 90:
                return "WATCH"
            if confidence >= 55:
                return "WAIT"
            return "IGNORE"

        if regime == "RISKY":
            if confidence >= 88:
                return "BUY"
            if confidence >= 65:
                return "WATCH"
            if confidence >= 45:
                return "WAIT"
            return "IGNORE"

        if regime == "NEUTRAL":
            if confidence >= 78:
                return "BUY"
            if confidence >= 60:
                return "WATCH"
            if confidence >= 40:
                return "WAIT"
            return "IGNORE"

        if regime == "BULLISH":
            if confidence >= 70:
                return "BUY"
            if confidence >= 55:
                return "WATCH"
            if confidence >= 35:
                return "WAIT"
            return "IGNORE"

        return "IGNORE"