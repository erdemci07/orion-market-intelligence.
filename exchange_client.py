import pandas as pd
from binance.client import Client

from config import BINANCE_API_KEY, BINANCE_API_SECRET, MODE


client = Client(
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    testnet=(MODE == "TESTNET")
)


def get_klines(symbol, interval="15m", limit=250):
    klines = client.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit
    )

    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df = df[["open", "high", "low", "close", "volume"]].astype(float)

    return df


def buy_market(symbol, usdt_amount):
    return client.create_order(
        symbol=symbol,
        side="BUY",
        type="MARKET",
        quoteOrderQty=usdt_amount
    )


def sell_market(symbol, quantity):
    return client.create_order(
        symbol=symbol,
        side="SELL",
        type="MARKET",
        quantity=quantity
    )