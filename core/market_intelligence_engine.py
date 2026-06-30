from services.exchange_client import ExchangeClient
from services.sentiment_client import SentimentClient
from strategy.indicators import build_indicator_snapshot
from core.altcoin_breadth_engine import AltcoinBreadthEngine


class MarketIntelligenceEngine:
    def __init__(self):
        self.exchange = ExchangeClient()
        self.altcoin_breadth = AltcoinBreadthEngine()
        self.sentiment = SentimentClient()

    def analyze(self):
        btc = self._analyze_symbol("BTCUSDT")
        eth = self._analyze_symbol("ETHUSDT")
        fear = self.sentiment.get_fear_greed_index()
        breadth = self.altcoin_breadth.analyze()

        btc_score = self._trend_score(btc)
        eth_score = self._trend_score(eth)
        fear_score = self._fear_score(int(fear["value"]))
        breadth_score = breadth["breadth_score"]

        market_score = (
            btc_score * 0.45 +
            eth_score * 0.25 +
            fear_score * 0.30 +
            breadth_score * 0.25
        )

        market_score = (
    btc_score * 0.35 +
    eth_score * 0.20 +
    fear_score * 0.20 +
    breadth_score * 0.25
)

        market_score = round(max(0, min(market_score, 100)), 2)

        regime = self._regime_from_score(market_score)

        return {
            "regime": regime["name"],
            "market_score": market_score,
            "min_score": regime["min_score"],
            "allow_new_positions": regime["allow_new_positions"],
            "btc_score": round(btc_score, 2),
            "eth_score": round(eth_score, 2),
            "fear_score": round(fear_score, 2),
            "fear_greed": fear,
            "btc": btc,
            "eth": eth,
            "breadth": breadth,
            "breadth_score": breadth_score,
            "reasons": regime["reasons"]
        }

    def _analyze_symbol(self, symbol):
        df = self.exchange.get_klines(
            symbol=symbol,
            interval="1h",
            limit=250
        )

        return build_indicator_snapshot(df)
    def _fear_score(self, fear_value):
        fear_value = int(fear_value)

        if fear_value <= 10:
            return 5
        if fear_value <= 20:
            return 15
        if fear_value <= 30:
            return 30
        if fear_value <= 40:
            return 45
        if fear_value <= 60:
            return 70
        if fear_value <= 75:
            return 60
        if fear_value <= 85:
            return 40

        return 25

    def _trend_score(self, snapshot):
        score = 0

        price = snapshot["price"]
        ema21 = snapshot["ema21"]
        ema50 = snapshot["ema50"]
        ema200 = snapshot["ema200"]
        rsi = snapshot["rsi"]
        macd = snapshot["macd_hist"]
        adx = snapshot["adx"]

        # Fiyat EMA21'e göre nerede?
        distance_ema21 = ((price - ema21) / ema21) * 100

        if distance_ema21 >= 2:
            score += 20
        elif distance_ema21 >= 0:
            score += 15
        elif distance_ema21 >= -1:
            score += 8

        # EMA21 - EMA50 ilişkisi
        ema21_50_diff = ((ema21 - ema50) / ema50) * 100

        if ema21_50_diff >= 2:
            score += 25
        elif ema21_50_diff >= 0:
            score += 18
        elif ema21_50_diff >= -1:
            score += 8

        # EMA50 - EMA200 ilişkisi
        ema50_200_diff = ((ema50 - ema200) / ema200) * 100

        if ema50_200_diff >= 3:
            score += 20
        elif ema50_200_diff >= 0:
            score += 12
        elif ema50_200_diff >= -1:
            score += 5

        # RSI
        if rsi >= 60:
            score += 15
        elif rsi >= 50:
            score += 10
        elif rsi >= 40:
            score += 5

        # MACD histogram
        if macd > 0:
            score += 10

        # ADX
        if adx >= 25:
            score += 10
        elif adx >= 20:
            score += 6

        return round(max(0, min(score, 100)), 2)

    def _regime_from_score(self, score):
        if score >= 75:
            return {
                "name": "BULLISH",
                "min_score": 60,
                "allow_new_positions": True,
                "reasons": ["Market skoru güçlü"]
            }

        if score >= 50:
            return {
                "name": "NEUTRAL",
                "min_score": 75,
                "allow_new_positions": True,
                "reasons": ["Market orta bölgede"]
            }

        if score >= 30:
            return {
                "name": "RISKY",
                "min_score": 88,
                "allow_new_positions": True,
                "reasons": ["Market zayıf ama tamamen panik değil"]
            }

        return {
            "name": "PANIC",
            "min_score": 95,
            "allow_new_positions": False,
            "reasons": ["Market skoru çok zayıf"]
        }