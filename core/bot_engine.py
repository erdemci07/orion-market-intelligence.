import time

from config import (
    MAX_OPEN_POSITIONS,
    POSITION_USDT_AMOUNT,
    FULL_SCAN_SECONDS,
    PERFORMANCE_REPORT_SECONDS,
)
from database.repository import is_symbol_in_cooldown
from database.repository import open_position, add_or_update_watchlist
from services.logger import OrionLogger            
from core.market_intelligence_engine import MarketIntelligenceEngine
from core.position_engine import PositionEngine
from core.scanner_engine import ScannerEngine
from core.order_engine import OrderEngine
from core.recovery_engine import RecoveryEngine
from core.confidence_engine import ConfidenceEngine
from core.decision_engine import DecisionEngine
from core.risk_engine import RiskEngine
from core.sector_intelligence_engine import SectorIntelligenceEngine
from core.watchlist_engine import WatchlistEngine
from core.cooldown_engine import CooldownEngine
from services.telegram_notifier import TelegramNotifier
from core.performance_engine import PerformanceEngine
from core.position_sizing_engine import PositionSizingEngine



class BotEngine:
    def __init__(self):
        self.position_sizing_engine = PositionSizingEngine()
        self.last_performance_report_time = 0
        self.notifier = TelegramNotifier()
        self.performance_engine = PerformanceEngine()
        self.logger = OrionLogger()
        self.market_engine = MarketIntelligenceEngine()
        self.position_engine = PositionEngine()
        self.scanner_engine = ScannerEngine()
        self.order_engine = OrderEngine()
        self.recovery_engine = RecoveryEngine()
        self.confidence_engine = ConfidenceEngine()
        self.decision_engine = DecisionEngine()
        self.risk_engine = RiskEngine()
        self.sector_engine = SectorIntelligenceEngine()
        self.watchlist_engine = WatchlistEngine()
        self.cooldown_engine = CooldownEngine()
        self.last_full_scan_time = 0
        self.last_regime = None
        self.last_sectors = []
        
    def _maybe_send_performance_report(self):
        now = time.time()

        if (
            self.last_performance_report_time == 0
            or now - self.last_performance_report_time >= PERFORMANCE_REPORT_SECONDS
        ):
            self.performance_engine.send_summary()
            self.last_performance_report_time = now

    def run_once(self):
        print("=" * 40)
        print("BotEngine çalıştı")
        print("=" * 40)
        self.logger.info("BotEngine çalıştı.")

        print("Bot çalıştı. Pozisyonlar kontrol ediliyor...")
        open_positions = self.position_engine.run()
        self._maybe_send_performance_report()

        now = time.time()
        should_full_scan = (
            self.last_full_scan_time == 0
            or now - self.last_full_scan_time >= FULL_SCAN_SECONDS
        )

        if not should_full_scan:
            if self.last_regime:
                self.watchlist_engine.run(
                    regime=self.last_regime,
                    confidence_engine=self.confidence_engine,
                    decision_engine=self.decision_engine,
                    risk_engine=self.risk_engine,
                )

            print("Tam tarama zamanı gelmedi. Sadece pozisyon/watchlist kontrol edildi.")
            return

        regime = self.market_engine.analyze()
        self.last_regime = regime
        self.last_full_scan_time = now

        self._send_market_regime_message(regime)

        sector_result = self.sector_engine.analyze()
        sectors = sector_result.get("sectors", [])
        self.last_sectors = sectors
        self._send_sector_message(sectors)

        watch_upgrades = self.watchlist_engine.run(
            regime=regime,
            confidence_engine=self.confidence_engine,
            decision_engine=self.decision_engine,
            risk_engine=self.risk_engine,
        )

        if watch_upgrades:
            approved = watch_upgrades
        else:
            if len(open_positions) >= MAX_OPEN_POSITIONS:
                self.notifier.send(
                    f"ℹ️ Maksimum açık pozisyon sayısına ulaşıldı: {len(open_positions)}"
                )
                return

            approved = self.scanner_engine.scan()

        if not approved:
            self.notifier.send("🔴 Uygun coin bulunamadı.")
            return

        recovery = self.recovery_engine.analyze(
            regime=regime,
            approved_coins=approved,
        )

        if recovery["active"]:
            self._send_recovery_message(recovery)

            if not recovery["allow_entry"]:
                return

            approved = recovery["candidates"]

        best = approved[0]

        symbol = best["symbol"]
        if not self.cooldown_engine.can_trade(symbol):
            self.notifier.send(
                f"""
⏳ <b>Cooldown Aktif</b>

Coin: <b>{symbol}</b>
Sebep: Yakın zamanda kapatıldı, tekrar alım bekletiliyor.
"""
            )
            return

        data = best["snapshot"]
        coin_score = best["score"]

        market_score = regime["market_score"]
        risk_score = self.risk_engine.calculate_risk_score(regime)

        sector_info = self.sector_engine.get_sector_score_for_symbol(
            symbol=symbol,
            sectors=sectors,
        )
        sector_score = sector_info["sector_score"]

        confidence = self.confidence_engine.calculate(
            coin_score=coin_score,
            market_score=market_score,
            sector_score=sector_score,
            risk_score=risk_score,
        )

        decision = self.decision_engine.decide(
            confidence=confidence,
            regime=regime["regime"],
        )

        self._send_decision_message(
            symbol=symbol,
            coin_score=coin_score,
            market_score=market_score,
            sector_info=sector_info,
            sector_score=sector_score,
            risk_score=risk_score,
            confidence=confidence,
            decision=decision,
        )

        if decision in ["WATCH", "WAIT"]:
            add_or_update_watchlist(
                symbol=symbol,
                coin_score=coin_score,
                market_score=market_score,
                sector_score=sector_score,
                risk_score=risk_score,
                confidence=confidence,
                decision=decision,
                reason="ORION karar motoru WATCH verdi",
            )

            self.notifier.send(
                f"""
👀 <b>Watchlist'e Alındı</b>

Coin: <b>{symbol}</b>
Confidence: %{confidence}
Sebep: BUY için erken, izlemeye alındı.
"""
            )
            return

        if decision != "BUY":
            return

        balance = self.order_engine.exchange.get_usdt_balance()

        usdt_amount = self.position_sizing_engine.calculate_usdt_amount(
    balance=balance,
    confidence=confidence,
    risk_score=risk_score,
    regime_name=regime["regime"]
)

        if usdt_amount <= 0:
            self.notifier.send(
                f"⚠️ Bakiye veya risk uygun değil. USDT bakiye: {balance}"
            )
            return

        quantity = usdt_amount / data["price"]

        order_result = self.order_engine.buy(
            symbol=symbol,
            usdt_amount=usdt_amount,
        )

        print("Order result:", order_result)

        entry_price = order_result.get("executed_price") or data["price"]
        executed_quantity = order_result.get("executed_quantity") or quantity

        added = open_position(
            symbol=symbol,
            entry_price=entry_price,
            quantity=executed_quantity,
            score=coin_score,
        )

        if added:
            self.notifier.send(
                f"""
🟢 <b>Yeni Otonom Pozisyon Açıldı</b>

Coin: <b>{symbol}</b>
Giriş: {round(data["price"], 6)}
Miktar: {round(quantity, 6)}
Order ID: {order_result.get("order_id")}
Skor: {round(coin_score, 2)}/100
Confidence: %{confidence}
Sektör: {sector_info["sector"]}
Sektör Skoru: {round(sector_score, 2)}
Emir Modu: {order_result.get("mode", "LIVE/TESTNET")}

Mod: Simülasyon / Veritabanı Kaydı
"""
            )
        else:
            self.notifier.send(
                f"""
ℹ️ <b>{symbol}</b> zaten açık pozisyonlarda var.

Emir Modu: {order_result.get("mode", "LIVE/TESTNET")}
"""
            )

    def _send_market_regime_message(self, regime):
        self.notifier.send(
            f"""
🌦️ <b>Market Intelligence</b>

Durum: <b>{regime["regime"]}</b>
Market Skoru: {regime["market_score"]}/100

BTC Skoru: {regime["btc_score"]}/100
ETH Skoru: {regime["eth_score"]}/100
Fear Skoru: {regime["fear_score"]}/100

Altcoin Breadth: {regime["breadth_score"]}/100
EMA Pozitif: %{regime["breadth"]["ema_positive_rate"]}
MACD Pozitif: %{regime["breadth"]["macd_positive_rate"]}
Yapı Pozitif: %{regime["breadth"]["structure_positive_rate"]}

Fear & Greed: {regime["fear_greed"]["value"]}
Sınıf: {regime["fear_greed"]["classification"]}

Yeni Pozisyon İzni: {regime["allow_new_positions"]}
Minimum Coin Skoru: {regime["min_score"]}

Sebepler:
{chr(10).join(["• " + r for r in regime["reasons"]])}
"""
        )

    def _send_sector_message(self, sectors):
        sector_text = ""

        for sector in sectors[:5]:
            sector_text += (
                f"• <b>{sector['name']}</b> | "
                f"24s: {round(sector['market_cap_change_24h'], 2)}% | "
                f"Skor: {sector['score']}\n"
            )

        if not sector_text:
            sector_text = "Sektör verisi alınamadı."

        self.notifier.send(
            f"""
🧭 <b>Sektör Zekâsı</b>

En güçlü sektörler:
{sector_text}
"""
        )

    def _send_recovery_message(self, recovery):
        watchlist_text = ""

        for item in recovery.get("watchlist", []):
            watchlist_text += (
                f"• <b>{item['symbol']}</b> | "
                f"Watch: {item['watch_score']} | "
                f"Skor: {round(item['main_score'], 2)} | "
                f"RSI: {item['rsi']} | "
                f"Hacim: {item['volume_score']}\n"
            )

        if not watchlist_text:
            watchlist_text = "Şimdilik güçlü izleme adayı yok."

        self.notifier.send(
            f"""
🧊 <b>Recovery Watchlist</b>

Durum: Aktif
Mesaj: {recovery["message"]}

İzlenecek Coinler:
{watchlist_text}
"""
        )

    def _send_decision_message(
        self,
        symbol,
        coin_score,
        market_score,
        sector_info,
        sector_score,
        risk_score,
        confidence,
        decision,
    ):
        self.logger.info(
            f"Karar: {symbol} | coin={coin_score} | market={market_score} | "
            f"sector={sector_score} | risk={risk_score} | confidence={confidence} | decision={decision}"
        )

        self.notifier.send(
            f"""
🧠 <b>ORION Karar Motoru</b>

Coin: <b>{symbol}</b>

Coin Skoru: {round(coin_score, 2)}
Market Skoru: {round(market_score, 2)}
Sektör: {sector_info["sector"]}
Sektör Skoru: {round(sector_score, 2)}
Risk Skoru: {round(risk_score, 2)}

Confidence: <b>%{confidence}</b>
Karar: <b>{decision}</b>
"""
        )
