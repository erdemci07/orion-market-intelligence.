from services.exchange_client import ExchangeClient


class SymbolSelector:
    def __init__(self):
        self.exchange = ExchangeClient()

    def get_symbols(self, limit=80):
        symbols = self.exchange.get_exchange_symbols()
        tickers = self.exchange.get_24h_tickers()

        ticker_map = {item["symbol"]: item for item in tickers}

        selected = []

        for symbol in symbols:
            ticker = ticker_map.get(symbol)
            if not ticker:
                continue

            quote_volume = float(ticker.get("quoteVolume", 0))
            price_change = float(ticker.get("priceChangePercent", 0))

            if quote_volume < 10_000_000:
                continue

            if price_change < -20:
                continue

            selected.append({
                "symbol": symbol,
                "quote_volume": quote_volume,
                "price_change": price_change
            })

        selected = sorted(
            selected,
            key=lambda x: x["quote_volume"],
            reverse=True
        )

        return [item["symbol"] for item in selected[:limit]]