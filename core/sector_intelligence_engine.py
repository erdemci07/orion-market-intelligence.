from services.sector_client import SectorClient


class SectorIntelligenceEngine:
    def __init__(self):
        self.client = SectorClient()

    def analyze(self):
        sectors = self.client.get_top_sector_scores(limit=20)

        if not sectors:
            return {
                "sectors": [],
                "default_sector_score": 50
            }

        return {
            "sectors": sectors,
            "default_sector_score": 50
        }

    def get_sector_score_for_symbol(self, symbol, sectors):
        symbol_key = symbol.replace("USDT", "").lower()

        best_score = 50
        best_sector = "Unknown"

        for sector in sectors:
            top_ids = sector.get("top_3_coins_id", [])

            for coin_id in top_ids:
                if symbol_key in coin_id.lower() or coin_id.lower() in symbol_key:
                    if sector["score"] > best_score:
                        best_score = sector["score"]
                        best_sector = sector["name"]

        return {
            "sector": best_sector,
            "sector_score": best_score
        }