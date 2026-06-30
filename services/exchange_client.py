import pandas as pd
from binance.client import Client

from config import BINANCE_API_KEY, BINANCE_API_SECRET, MODE


class ExchangeClient:
    def __init__(self):
        self.client = Client(
            BINANCE_API_KEY,
            BINANCE_API_SECRET,
            testnet=(MODE == "TESTNET")
        )

    def get_klines(self, symbol, interval="15m", limit=250):
        klines = self.client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )

        df = pd.DataFrame(klines, columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore"
        ])

        df = df[["open", "high", "low", "close", "volume"]].astype(float)

        return df
    
    def get_usdt_balance(self):
        account = self.client.get_account()

        for balance in account["balances"]:
            if balance["asset"] == "USDT":
               return float(balance["free"])

        return 0.0

    def buy_market(self, symbol, usdt_amount):
        return self.client.create_order(
            symbol=symbol,
            side="BUY",
            type="MARKET",
            quoteOrderQty=usdt_amount
        )

    def get_24h_tickers(self):
        return self.client.get_ticker()

    def get_exchange_symbols(self):
        info = self.client.get_exchange_info()

        symbols = []

        for item in info["symbols"]:
            if item["status"] != "TRADING":
                continue

            symbol = item["symbol"]

            if not symbol.endswith("USDT"):
                continue

            blocked = [
                "UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT",
                "USDCUSDT", "BUSDUSDT", "FDUSDUSDT", "TUSDUSDT"
            ]

            if any(b in symbol for b in blocked):
                continue

            symbols.append(symbol)

        return symbols