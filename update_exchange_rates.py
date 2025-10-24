import time
import ccxt
from datetime import datetime, UTC
from sql.sql import SQL
from sql.sql_model import ExchangeRate


class ExchangeRateUpdater:
    def __init__(self, interval_minutes=5):
        self.interval = interval_minutes * 60
        self.sql = SQL()
        self.exchange = ccxt.binance()
        self.pairs = ["USDT/RUB", "BTC/RUB", "ETH/RUB", "BTC/USDT", "ETH/USDT",
                      "SOL/USDT", "TRX/USDT", "ETH/EUR", "BTC/EUR", "EUR/USDT", "SOL/EUR"]

    def fetch_rate(self, pair):
        """Получаем курс пары"""
        try:
            ticker = self.exchange.fetch_ticker(pair)
            return ticker["last"]
        except Exception as e:
            print(f"❌ Ошибка получения курса {pair}: {e}")
            return None

    def update_db(self):
        """Записываем курс в БД"""
        for pair in self.pairs:
            rate = self.fetch_rate(pair)
            if rate:
                obj = ExchangeRate(
                    pair=pair,
                    rate=rate,
                    updated_at=datetime.now(UTC)
                )
                self.sql.add_exchange_rate(obj)
                print(f"✅ Обновлён курс {pair}: {rate}")

    def start(self):
        """Бесконечный цикл"""
        while True:
            print(f"\n🔁 Обновление курсов... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.update_db()
            print(f"⏳ Следующее обновление через {self.interval / 60} минут")
            time.sleep(self.interval)


if __name__ == "__main__":
    updater = ExchangeRateUpdater(interval_minutes=5)
    updater.start()
