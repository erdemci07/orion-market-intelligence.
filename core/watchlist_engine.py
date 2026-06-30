from database.repository import get_active_watchlist, remove_from_watchlist

from services.exchange_client import ExchangeClient
from services.telegram_notifier import TelegramNotifier

from strategy.indicators import build_indicator_snapshot
from strategy.scoring import score_symbol


class WatchlistEngine:
    def __init__(self):
        self.exchange = ExchangeClient()
        self.notifier = TelegramNotifier()

    def run(self, regime, confidence_engine, decision_engine, risk_engine):
        watch_items = get_active_watchlist()

        if not watch_items:
            return []

        upgraded = []

        for item in watch_items:
            symbol = item["symbol"]

            try:
                df = self.exchange.get_klines(
                    symbol=symbol,
                    interval="15m",
                    limit=250
                )

                snapshot = build_indicator_snapshot(df)
                score_result = score_symbol(snapshot)

                coin_score = score_result["final_score"]
                market_score = regime["market_score"]
                sector_score = item.get("sector_score") or 50
                risk_score = risk_engine.calculate_risk_score(regime)

                confidence = confidence_engine.calculate(
                    coin_score=coin_score,
                    market_score=market_score,
                    sector_score=sector_score,
                    risk_score=risk_score
                )

                decision = decision_engine.decide(
                    confidence=confidence,
                    regime=regime["regime"]
                )

                print(
                    "WATCH:",
                    symbol,
                    "coin:",
                    coin_score,
                    "confidence:",
                    confidence,
                    "decision:",
                    decision
                )

                if decision == "BUY":
                    upgraded.append({
                        "symbol": symbol,
                        "snapshot": snapshot,
                        "score": coin_score,
                        "confidence": confidence
                    })

                    remove_from_watchlist(symbol)

                    self.notifier.send(
                        f"""
🔥 <b>WATCH → BUY</b>

Coin: <b>{symbol}</b>
Yeni Coin Skoru: {round(coin_score, 2)}
Confidence: %{confidence}

Karar: BUY
"""
                    )

            except Exception as e:
                print(symbol, "watchlist takip hatası:", e)

        return upgraded