import time
from database.database import init_database
from core.bot_engine import BotEngine
from config import POSITION_CHECK_SECONDS


if __name__ == "__main__":
    init_database()

    bot = BotEngine()

    while True:
        try:
            bot.run_once()
        except Exception as e:
            print("Bot genel hata:", e)

        print(f"{POSITION_CHECK_SECONDS} saniye bekleniyor...")
        time.sleep(POSITION_CHECK_SECONDS)