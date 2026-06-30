class RecoveryEngine:
    def analyze(self, regime, approved_coins):
        fear_value = regime["fear_greed"]["value"]
        btc_15m = regime["btc_15m"]

        if fear_value > 25:
            return {
                "active": False,
                "allow_entry": False,
                "message": "Recovery modu aktif değil.",
                "watchlist": []
            }

        watchlist = self.build_watchlist(approved_coins)

        btc_recovery_signal = (
            btc_15m["ema21"] > btc_15m["ema50"]
            and btc_15m["rsi"] >= 35
            and btc_15m["macd_hist"] > 0
        )

        if not btc_recovery_signal:
            return {
                "active": True,
                "allow_entry": False,
                "message": "Extreme fear var ama BTC toparlanma sinyali henüz yok.",
                "watchlist": watchlist
            }

        recovery_candidates = []

        for coin in approved_coins:
            snapshot = coin["snapshot"]
            scores = coin["scores"]

            if (
                snapshot["rsi"] >= 35
                and snapshot["macd_hist"] > 0
                and scores["structure"] >= 60
                and scores["volume"] >= 30
            ):
                recovery_candidates.append(coin)

        recovery_candidates = sorted(
            recovery_candidates,
            key=lambda x: x["score"],
            reverse=True
        )

        if not recovery_candidates:
            return {
                "active": True,
                "allow_entry": False,
                "message": "BTC toparlanıyor ama uygun dönüş coini bulunamadı.",
                "watchlist": watchlist
            }

        return {
            "active": True,
            "allow_entry": True,
            "message": "Recovery modu girişe izin verdi.",
            "candidates": recovery_candidates,
            "watchlist": watchlist
        }

    def build_watchlist(self, approved_coins):
        watchlist = []

        for coin in approved_coins:
            scores = coin["scores"]
            snapshot = coin["snapshot"]

            watch_score = (
                scores["structure"] * 0.40 +
                scores["adx"] * 0.25 +
                scores["ema"] * 0.20 +
                scores["volume"] * 0.15
            )

            if watch_score >= 45:
                watchlist.append({
                    "symbol": coin["symbol"],
                    "watch_score": round(watch_score, 2),
                    "main_score": coin["score"],
                    "rsi": round(snapshot["rsi"], 2),
                    "volume_score": round(scores["volume"], 2)
                })

        return sorted(
            watchlist,
            key=lambda x: x["watch_score"],
            reverse=True
        )[:5]