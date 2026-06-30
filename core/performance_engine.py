from database.repository import get_performance_summary
from services.telegram_notifier import TelegramNotifier


class PerformanceEngine:
    def __init__(self):
        self.notifier = TelegramNotifier()

    def send_summary(self):
        summary = get_performance_summary()

        self.notifier.send(
            f"""
📊 <b>ORION Performans Özeti</b>

Açık Pozisyon: {summary["open_positions"]}

Kapanan İşlem: {summary["total_closed_trades"]}
Kazanan İşlem: {summary["winning_trades"]}
Kaybeden İşlem: {summary["losing_trades"]}

Win Rate: %{summary["win_rate"]}
Toplam Kâr/Zarar: {summary["total_profit"]}
"""
        )