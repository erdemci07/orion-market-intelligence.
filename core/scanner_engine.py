from services.exchange_client import ExchangeClient
from strategy.indicators import build_indicator_snapshot
from strategy.scoring import score_symbol
from strategy.symbol_selector import SymbolSelector

from config import INTERVAL, KLINE_LIMIT, MIN_FINAL_SCORE


class ScannerEngine:
    def __init__(self):
        self.exchange = ExchangeClient()
        self.symbol_selector = SymbolSelector()

    def scan(self):
        approved = []

        for symbol in self.symbol_selector.get_symbols():
            try:
                df = self.exchange.get_klines(
                    symbol=symbol,
                    interval=INTERVAL,
                    limit=KLINE_LIMIT
                )

                snapshot = build_indicator_snapshot(df)
                result = score_symbol(snapshot)

                final_score = result["final_score"]

                print(symbol, final_score, result["scores"])

                if final_score >= MIN_FINAL_SCORE:
                    approved.append({
                        "symbol": symbol,
                        "snapshot": snapshot,
                        "score": final_score,
                        "scores": result["scores"]
                    })

            except Exception as e:
                print(symbol, "tarama hatası:", e)

        return sorted(
            approved,
            key=lambda x: x["score"],
            reverse=True
        )