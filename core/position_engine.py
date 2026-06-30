from database.repository import get_open_positions, update_position, close_position
from services.exchange_client import ExchangeClient
from services.telegram_notifier import TelegramNotifier
from strategy.indicators import build_indicator_snapshot
from strategy.scoring import score_symbol


class PositionEngine:
    def __init__(self):
        self.exchange = ExchangeClient()
        self.notifier = TelegramNotifier()

    def run(self):
        positions = get_open_positions()

        print("Açık pozisyon sayısı:", len(positions))

        for position in positions:
            self.manage_position(position)

        return get_open_positions()

    def manage_position(self, position):
        symbol = position["symbol"]

        try:
            df = self.exchange.get_klines(
                symbol=symbol,
                interval="15m",
                limit=250
            )

            snapshot = build_indicator_snapshot(df)
            score_result = score_symbol(snapshot)

        except Exception as e:
            print(symbol, "pozisyon veri hatası:", e)
            return

        current_price = snapshot["price"]

        entry_price = position["entry_price"]
        quantity = position["quantity"]
        highest_price = position["highest_price"]
        stop_price = position["stop_price"]
        target_price = position["target_price"]

        if current_price > highest_price:
            highest_price = current_price

        profit_percent = ((current_price - entry_price) / entry_price) * 100
        position_score = self.calculate_position_score(snapshot, score_result)

        new_stop = self.calculate_dynamic_stop(
            entry_price=entry_price,
            current_price=current_price,
            highest_price=highest_price,
            old_stop=stop_price,
            atr=snapshot["atr"],
            profit_percent=profit_percent,
            position_score=position_score
        )

        new_target = self.calculate_dynamic_target(
            current_price=current_price,
            old_target=target_price,
            profit_percent=profit_percent,
            position_score=position_score
        )

        update_position(symbol, {
            "highest_price": highest_price,
            "stop_price": new_stop,
            "target_price": new_target
        })

        action, reason = self.decide_exit(
            current_price=current_price,
            stop_price=new_stop,
            target_price=new_target,
            profit_percent=profit_percent,
            position_score=position_score,
            snapshot=snapshot
        )

        print(
            symbol,
            "güncel:", round(current_price, 6),
            "kâr:", round(profit_percent, 2),
            "skor:", position_score,
            "stop:", round(new_stop, 6),
            "hedef:", round(new_target, 6),
            "karar:", action
        )

        if action == "SELL_ALL":
            closed = close_position(symbol, current_price)

            if closed:
                self.notifier.send(
                    f"""
🔴 <b>Pozisyon Kapatıldı</b>

Coin: <b>{symbol}</b>
Giriş: {round(entry_price, 6)}
Çıkış: {round(current_price, 6)}
Miktar: {round(quantity, 6)}

Kâr/Zarar: %{round(profit_percent, 2)}
Pozisyon Skoru: {position_score}/100

Sebep: {reason}
"""
                )

        elif action == "WARN":
            self.notifier.send(
                f"""
⚠️ <b>Pozisyon Uyarısı</b>

Coin: <b>{symbol}</b>
Giriş: {round(entry_price, 6)}
Güncel: {round(current_price, 6)}

Kâr/Zarar: %{round(profit_percent, 2)}
Pozisyon Skoru: {position_score}/100

Sebep: {reason}
"""
            )

    def calculate_position_score(self, snapshot, score_result):
        score = 0

        scores = score_result["scores"]

        score += scores["structure"] * 0.25
        score += scores["ema"] * 0.20
        score += scores["adx"] * 0.15
        score += scores["volume"] * 0.15
        score += scores["rsi"] * 0.10
        score += scores["macd"] * 0.10
        score += scores["fibonacci"] * 0.05

        if snapshot["sudden_drop"]:
            score -= 25

        if snapshot["abnormal_volume"]:
            score -= 15

        return round(max(0, min(score, 100)), 2)

    def calculate_dynamic_stop(
        self,
        entry_price,
        current_price,
        highest_price,
        old_stop,
        atr,
        profit_percent,
        position_score
    ):
        new_stop = old_stop

        # İlk kâr oluşunca zararı sıfıra yaklaştır
        if profit_percent >= 3:
            new_stop = max(new_stop, entry_price)

        # Kâr büyürse trailing stop başlat
        if profit_percent >= 6:
            atr_stop = highest_price - (atr * 2)
            new_stop = max(new_stop, atr_stop)

        # Pozisyon zayıflıyorsa stopu daha agresif yukarı çek
        if profit_percent > 2 and position_score < 50:
            defensive_stop = current_price * 0.985
            new_stop = max(new_stop, defensive_stop)

        # Pozisyon çok güçlüyse biraz daha nefes bırak
        if position_score >= 80 and profit_percent >= 6:
            relaxed_stop = highest_price - (atr * 2.5)
            new_stop = max(old_stop, relaxed_stop)

        return round(new_stop, 8)

    def calculate_dynamic_target(
        self,
        current_price,
        old_target,
        profit_percent,
        position_score
    ):
        new_target = old_target

        # Pozisyon çok güçlüyse hedefi yukarı taşı
        if profit_percent >= 6 and position_score >= 80:
            new_target = max(new_target, current_price * 1.08)

        # Kâr var ama skor zayıflıyorsa hedefi aşağı yaklaştır
        if profit_percent >= 4 and position_score < 55:
            new_target = min(new_target, current_price * 1.03)

        return round(new_target, 8)

    def decide_exit(
        self,
        current_price,
        stop_price,
        target_price,
        profit_percent,
        position_score,
        snapshot
    ):
        if current_price <= stop_price:
            return "SELL_ALL", "Stop / trailing stop tetiklendi"

        if snapshot["sudden_drop"] and snapshot["abnormal_volume"]:
            return "SELL_ALL", "Ani düşüş ve anormal hacim"

        if profit_percent <= -5:
            return "SELL_ALL", "Maksimum zarar sınırı aşıldı"

        if position_score <= 25:
            return "SELL_ALL", "Pozisyon skoru çok zayıfladı"

        if profit_percent >= 5 and position_score < 45:
            return "SELL_ALL", "Kâr varken grafik zayıfladı"

        if current_price >= target_price and position_score < 70:
            return "SELL_ALL", "Hedef geldi ve güç azaldı"

        if current_price >= target_price and position_score >= 70:
            return "WARN", "Hedef bölgesine geldi ama trend güçlü, izleniyor"

        return "HOLD", "Pozisyon korunuyor"