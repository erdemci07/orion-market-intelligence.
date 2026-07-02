from config import (
    STOP_LOSS_PERCENT,
    HARD_STOP_LOSS_PERCENT,
    BREAK_EVEN_PROFIT_PERCENT,
    TRAILING_START_PROFIT_PERCENT,
    TRAILING_ATR_MULTIPLIER,
    WEAK_SCORE_EXIT,
    DANGER_SCORE_EXIT,
    PROFIT_PROTECT_SCORE,
)

from database.repository import (
    get_open_positions,
    update_position,
    close_position,
    partial_close_position,
)

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
        highest_price = position["highest_price"] or entry_price
        old_stop = position["stop_price"] or self.initial_stop(entry_price)
        old_target = position["target_price"] or entry_price * 1.10

        if current_price > highest_price:
            highest_price = current_price

        profit_percent = ((current_price - entry_price) / entry_price) * 100
        position_score = self.calculate_position_score(snapshot, score_result)

        new_stop = self.calculate_dynamic_stop(
            entry_price=entry_price,
            current_price=current_price,
            highest_price=highest_price,
            old_stop=old_stop,
            atr=snapshot["atr"],
            profit_percent=profit_percent,
            position_score=position_score,
        )

        new_target = self.calculate_dynamic_target(
            current_price=current_price,
            old_target=old_target,
            profit_percent=profit_percent,
            position_score=position_score,
        )

        update_position(symbol, {
            "highest_price": highest_price,
            "stop_price": new_stop,
            "target_price": new_target,
        })

        action, reason = self.decide_exit(
            current_price=current_price,
            entry_price=entry_price,
            stop_price=new_stop,
            target_price=new_target,
            profit_percent=profit_percent,
            position_score=position_score,
            snapshot=snapshot,
        )

        print(
            symbol,
            "güncel:", round(current_price, 6),
            "kâr:", round(profit_percent, 2),
            "skor:", position_score,
            "stop:", round(new_stop, 6),
            "hedef:", round(new_target, 6),
            "karar:", action,
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

        elif action == "SELL_HALF":
            sold = partial_close_position(
                symbol=symbol,
                exit_price=current_price,
                close_ratio=0.50,
            )

            if sold:
                self.notifier.send(
                    f"""
🟠 <b>Kısmi Satış Yapıldı</b>

Coin: <b>{symbol}</b>
Giriş: {round(entry_price, 6)}
Çıkış: {round(current_price, 6)}
Satılan: %{50}

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
Güncel: {round(current_price, 6)}
Kâr/Zarar: %{round(profit_percent, 2)}
Pozisyon Skoru: {position_score}/100

Sebep: {reason}
"""
            )

    def initial_stop(self, entry_price):
        return entry_price * (1 - STOP_LOSS_PERCENT / 100)

    def calculate_position_score(self, snapshot, score_result):
        scores = score_result["scores"]

        score = (
            scores["structure"] * 0.25 +
            scores["ema"] * 0.20 +
            scores["adx"] * 0.15 +
            scores["volume"] * 0.15 +
            scores["rsi"] * 0.10 +
            scores["macd"] * 0.10 +
            scores["fibonacci"] * 0.05
        )

        if snapshot["sudden_drop"]:
            score -= 20

        if snapshot["abnormal_volume"]:
            score -= 10

        return round(max(0, min(score, 100)), 2)

    def calculate_dynamic_stop(
        self,
        entry_price,
        current_price,
        highest_price,
        old_stop,
        atr,
        profit_percent,
        position_score,
    ):
        hard_stop = entry_price * (1 - HARD_STOP_LOSS_PERCENT / 100)
        initial_stop = entry_price * (1 - STOP_LOSS_PERCENT / 100)

        new_stop = max(old_stop, hard_stop, initial_stop)

        if profit_percent >= BREAK_EVEN_PROFIT_PERCENT:
            new_stop = max(new_stop, entry_price)

        if profit_percent >= TRAILING_START_PROFIT_PERCENT:
            atr_stop = highest_price - (atr * TRAILING_ATR_MULTIPLIER)
            new_stop = max(new_stop, atr_stop)

        if profit_percent > 1 and position_score < PROFIT_PROTECT_SCORE:
            defensive_stop = current_price * 0.99
            new_stop = max(new_stop, defensive_stop)

        if profit_percent >= 5 and position_score >= 75:
            relaxed_stop = highest_price - (atr * 2.2)
            new_stop = max(old_stop, relaxed_stop)

        return round(new_stop, 8)

    def calculate_dynamic_target(
        self,
        current_price,
        old_target,
        profit_percent,
        position_score,
    ):
        new_target = old_target

        if profit_percent >= 4 and position_score >= 75:
            new_target = max(new_target, current_price * 1.06)

        if profit_percent >= 3 and position_score < 50:
            new_target = min(new_target, current_price * 1.02)

        return round(new_target, 8)

    def decide_exit(
        self,
        current_price,
        entry_price,
        stop_price,
        target_price,
        profit_percent,
        position_score,
        snapshot,
    ):
        hard_loss = -HARD_STOP_LOSS_PERCENT

        if profit_percent <= hard_loss:
            return "SELL_ALL", "Hard stop-loss tetiklendi"

        if current_price <= stop_price:
            return "SELL_ALL", "Stop / trailing stop tetiklendi"

        if snapshot["sudden_drop"] and snapshot["abnormal_volume"]:
            return "SELL_ALL", "Ani düşüş ve anormal hacim"

        if position_score <= DANGER_SCORE_EXIT:
            return "SELL_ALL", "Pozisyon skoru kritik seviyeye düştü"

        if profit_percent >= 2 and position_score <= WEAK_SCORE_EXIT:
            return "SELL_ALL", "Kârdayken grafik ciddi zayıfladı"

        if profit_percent >= 4 and position_score < 50:
            return "SELL_HALF", "Kâr var ama momentum zayıflıyor"

        if current_price >= target_price and position_score < 70:
            return "SELL_ALL", "Hedef geldi ve güç azaldı"

        if current_price >= target_price and position_score >= 70:
            return "WARN", "Hedef bölgesi geldi ama trend güçlü"

        return "HOLD", "Pozisyon korunuyor"