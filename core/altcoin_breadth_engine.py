from services.exchange_client import ExchangeClient
from strategy.indicators import build_indicator_snapshot
from strategy.market_filters import get_candidate_symbols


class AltcoinBreadthEngine:
    def __init__(self):
        self.exchange = ExchangeClient()

    def analyze(self):
        symbols = [
            s for s in get_candidate_symbols()
            if s not in ["BTCUSDT", "ETHUSDT"]
        ]

        total = 0
        ema_positive = 0
        macd_positive = 0
        structure_positive = 0

        for symbol in symbols:
            try:
                df = self.exchange.get_klines(
                    symbol=symbol,
                    interval="1h",
                    limit=250
                )

                snapshot = build_indicator_snapshot(df)

                total += 1

                if snapshot["price"] > snapshot["ema21"]:
                    ema_positive += 1

                if snapshot["macd_hist"] > 0:
                    macd_positive += 1

                if snapshot["higher_high"] or snapshot["higher_low"]:
                    structure_positive += 1

            except Exception as e:
                print(symbol, "breadth hatası:", e)

        if total == 0:
            return {
                "breadth_score": 50,
                "total": 0,
                "ema_positive_rate": 0,
                "macd_positive_rate": 0,
                "structure_positive_rate": 0
            }

        ema_rate = ema_positive / total
        macd_rate = macd_positive / total
        structure_rate = structure_positive / total

        breadth_score = (
            ema_rate * 40 +
            macd_rate * 30 +
            structure_rate * 30
        )

        return {
            "breadth_score": round(max(0, min(breadth_score, 100)), 2),
            "total": total,
            "ema_positive_rate": round(ema_rate * 100, 2),
            "macd_positive_rate": round(macd_rate * 100, 2),
            "structure_positive_rate": round(structure_rate * 100, 2)
        }