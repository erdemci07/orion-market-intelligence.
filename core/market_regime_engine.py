from services.exchange_client import ExchangeClient
from services.sentiment_client import SentimentClient
from strategy.indicators import build_indicator_snapshot


class MarketRegimeEngine:
    def __init__(self):
        self.exchange = ExchangeClient()
        self.sentiment = SentimentClient()

    def analyze_btc(self):
        df_1h = self.exchange.get_klines(
            symbol="BTCUSDT",
            interval="1h",
            limit=250
        )

        df_15m = self.exchange.get_klines(
            symbol="BTCUSDT",
            interval="15m",
            limit=250
        )

        btc_1h = build_indicator_snapshot(df_1h)
        btc_15m = build_indicator_snapshot(df_15m)

        fear = self.sentiment.get_fear_greed_index()

        score = 0
        reasons = []

        if btc_1h["ema21"] > btc_1h["ema50"]:
            score += 20
            reasons.append("1H EMA21 > EMA50")

        if btc_1h["ema50"] > btc_1h["ema200"]:
            score += 20
            reasons.append("1H EMA50 > EMA200")

        if btc_15m["ema21"] > btc_15m["ema50"]:
            score += 15
            reasons.append("15M kısa trend pozitif")

        if 40 <= btc_1h["rsi"] <= 65:
            score += 15
            reasons.append("1H RSI sağlıklı")
        elif 30 <= btc_1h["rsi"] < 40:
            score += 8
            reasons.append("1H RSI düşük ama toparlanabilir")

        if btc_1h["adx"] >= 25:
            score += 15
            reasons.append("1H ADX güçlü")
        elif btc_1h["adx"] >= 18:
            score += 8
            reasons.append("1H ADX orta")

        last_close = float(df_15m["close"].iloc[-1])
        prev_close = float(df_15m["close"].iloc[-2])
        change_15m = ((last_close - prev_close) / prev_close) * 100

        if change_15m <= -2.5:
            score -= 25
            reasons.append("15M sert BTC düşüşü")

        fear_value = fear["value"]

        if fear_value <= 20:
            score -= 20
            reasons.append(f"Extreme Fear: {fear_value}")

        elif fear_value <= 30:
            score -= 10
            reasons.append(f"Fear: {fear_value}")

        elif 40 <= fear_value <= 60:
            score += 5
            reasons.append(f"Nötr duygu: {fear_value}")

        elif fear_value >= 80:
            score -= 15
            reasons.append(f"Extreme Greed riski: {fear_value}")

        score = max(0, min(score, 100))

        if score >= 75:
            regime = "BULLISH"
            min_score = 60
            allow_new_positions = True

        elif score >= 50:
            regime = "NEUTRAL"
            min_score = 75
            allow_new_positions = True

        elif score >= 25:
            regime = "RISKY"
            min_score = 88
            allow_new_positions = True

        else:
            regime = "PANIC"
            min_score = 95
            allow_new_positions = False

        return {
            "regime": regime,
            "btc_score": score,
            "min_score": min_score,
            "allow_new_positions": allow_new_positions,
            "fear_greed": fear,
            "reasons": reasons,
            "btc_1h": btc_1h,
            "btc_15m": btc_15m,
            "change_15m": change_15m
        }