class ConfidenceEngine:
    def calculate(self, coin_score, market_score, sector_score=50, risk_score=50):
        coin_factor = coin_score / 100
        market_factor = market_score / 100
        sector_factor = sector_score / 100
        risk_factor = risk_score / 100

        base_confidence = (
            coin_factor * 0.40 +
            market_factor * 0.30 +
            sector_factor * 0.20 +
            risk_factor * 0.10
        ) * 100

        # Market kötüyse coini cezalandır
        if market_score < 20:
            base_confidence *= 0.45
        elif market_score < 35:
            base_confidence *= 0.60
        elif market_score < 50:
            base_confidence *= 0.80

        # Risk kötüyse ikinci ceza
        if risk_score < 25:
            base_confidence *= 0.60
        elif risk_score < 40:
            base_confidence *= 0.80

        # Sektör güçlüyse hafif destek
        if sector_score >= 80 and market_score >= 40:
            base_confidence *= 1.10

        return round(max(0, min(base_confidence, 100)), 2)