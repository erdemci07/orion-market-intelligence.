import requests

class SectorClient:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def get_categories(self):
        url = f"{self.BASE_URL}/coins/categories"

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print("Kategori verisi alınamadı:", e)
            return []

    def get_top_sector_scores(self, limit=20):
        categories = self.get_categories()

        blocked_keywords = [
    "ecosystem",
    "governance",
    "inscriptions",
    "olympus",
    "fan token",
    "arcade",
    "bridged",
    "wrapped",
    "stablecoin",
    "index",
    "tokenized",
    "stock",
    "bstocks"
]

        sector_scores = []

        for category in categories:
            market_cap = category.get("market_cap", 0)
            volume_24h = category.get("volume_24h", 0)
            name = category.get("name", "")

            if market_cap < 500_000_000:
                continue
            if volume_24h < 25_000_000:
                continue
            if any(word.lower() in name.lower() for word in blocked_keywords):
                continue

            market_cap_change = category.get("market_cap_change_24h")
            if market_cap_change is None:
                continue

            sector_scores.append({
                "name": name,
                "market_cap": market_cap,
                "volume_24h": volume_24h,
                "market_cap_change_24h": market_cap_change,
            })

        return sector_scores[:limit]
    def get_top_sector_scores(self, limit=20):
        categories = self.get_categories()

        sector_scores = []

        for category in categories:
            market_cap_change = category.get("market_cap_change_24h")

            if market_cap_change is None:
                continue

            score = self._normalize_change(market_cap_change)

            sector_scores.append({
                "id": category.get("id"),
                "name": category.get("name"),
                "market_cap_change_24h": market_cap_change,
                "score": score,
                "top_3_coins_id": category.get("top_3_coins_id", [])
            })

        return sorted(
            sector_scores,
            key=lambda x: x["score"],
            reverse=True
        )[:limit]

    def _normalize_change(self, change):
        # -10 ile +10 arası değişimi 0-100 puana çevirir
        score = 50 + (change * 5)
        return max(0, min(round(score, 2), 100))