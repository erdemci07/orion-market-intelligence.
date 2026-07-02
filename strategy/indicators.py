import numpy as np
import pandas as pd


def ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()


def rsi(df, period=14):
    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, 0.000001)

    result = 100 - (100 / (1 + rs))

    return result.fillna(50)

def detect_sudden_drop(df, threshold=-2.5):
    if len(df) < 2:
        return False

    prev_close = df["close"].iloc[-2]
    current_close = df["close"].iloc[-1]

    change = ((current_close - prev_close) / prev_close) * 100
    return change <= threshold


def detect_abnormal_volume(df, multiplier=3):
    if len(df) < 21:
        return False

    current_volume = df["volume"].iloc[-1]
    avg_volume = df["volume"].tail(20).mean()

    if avg_volume <= 0:
        return False

    return current_volume >= avg_volume * multiplier


def macd_hist(df):
    ema12 = ema(df, 12)
    ema26 = ema(df, 26)
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal


def atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def adx(df, period=14):
    high = df["high"]
    low = df["low"]

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)

    tr = atr(df, period) * period

    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(period).sum() / tr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period).sum() / tr

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.rolling(period).mean()


def fibonacci(df, lookback=60):
    recent = df.tail(lookback)
    high = recent["high"].max()
    low = recent["low"].min()
    diff = high - low

    return {
        "fib_382": high - diff * 0.382,
        "fib_500": high - diff * 0.500,
        "fib_618": high - diff * 0.618,
    }

def detect_sudden_drop(df, threshold=-2.0):
    if len(df) < 2:
        return False

    previous_close = df["close"].iloc[-2]
    current_close = df["close"].iloc[-1]

    change = ((current_close - previous_close) / previous_close) * 100

    return change <= threshold


def detect_abnormal_volume(df, multiplier=2.5):
    if len(df) < 21:
        return False

    current_volume = df["volume"].iloc[-1]
    avg_volume = df["volume"].tail(20).mean()

    if avg_volume <= 0:
        return False

    return current_volume >= avg_volume * multiplier


def market_structure(df, lookback=30):
    recent = df.tail(lookback)
    mid = lookback // 2

    first = recent.iloc[:mid]
    second = recent.iloc[mid:]

    higher_high = second["high"].max() > first["high"].max()
    higher_low = second["low"].min() > first["low"].min()

    return higher_high, higher_low


def build_indicator_snapshot(df):
    
    df = df.copy()

    df["ema21"] = ema(df, 21)
    df["ema50"] = ema(df, 50)
    df["ema200"] = ema(df, 200)
    df["rsi"] = rsi(df)
    df["macd_hist"] = macd_hist(df)
    df["atr"] = atr(df)
    df["adx"] = adx(df)

    fib = fibonacci(df)
    higher_high, higher_low = market_structure(df)

    last = df.iloc[-1]

    return {
        "price": float(last["close"]),
        "volume_24h": float(last["close"] * last["volume"]),
        "volume": float(last["volume"]),
        "avg_volume": float(df["volume"].tail(20).mean()),

        "ema21": float(last["ema21"]),
        "ema50": float(last["ema50"]),
        "ema200": float(last["ema200"]),

        "rsi": float(last["rsi"]),
        "macd_hist": float(last["macd_hist"]),
        "adx": float(last["adx"]),
        "atr": float(last["atr"]),

        "higher_high": bool(higher_high),
        "higher_low": bool(higher_low),

        "fib_382": float(fib["fib_382"]),
        "fib_500": float(fib["fib_500"]),
        "fib_618": float(fib["fib_618"]),

        "sudden_drop": detect_sudden_drop(df),
        "abnormal_volume": detect_abnormal_volume(df),
    }