class DecisionEngine:
    def decide(self, confidence, regime):
        if regime == "SURVIVAL":
            if confidence >= 88:
                return "BUY"
            if confidence >= 65:
                return "WATCH"
            if confidence >= 45:
                return "WAIT"
            return "IGNORE"

        if regime == "DEFENSIVE":
            if confidence >= 82:
                return "BUY"
            if confidence >= 62:
                return "WATCH"
            if confidence >= 42:
                return "WAIT"
            return "IGNORE"

        if regime == "CAREFUL":
            if confidence >= 76:
                return "BUY"
            if confidence >= 58:
                return "WATCH"
            if confidence >= 38:
                return "WAIT"
            return "IGNORE"

        if regime == "NORMAL":
            if confidence >= 70:
                return "BUY"
            if confidence >= 55:
                return "WATCH"
            return "IGNORE"

        if regime == "BULLISH":
            if confidence >= 65:
                return "BUY"
            if confidence >= 50:
                return "WATCH"
            return "IGNORE"

        if regime == "AGGRESSIVE":
            if confidence >= 60:
                return "BUY"
            if confidence >= 45:
                return "WATCH"
            return "IGNORE"

        return "IGNORE"