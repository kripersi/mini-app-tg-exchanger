import requests
import ccxt
from datetime import datetime, UTC
from sql.sql import SQL
from sql.sql_model import ExchangeRate
from utils.google_sheet import GoogleSheet
import time


class ExchangeRateUpdater:
    def __init__(self, sheet_credentials, sheet_name):
        self.sheet = GoogleSheet(sheet_credentials, sheet_name)
        self.sql = SQL()
        self.binance = ccxt.binance()
        self.currencyfreaks_api_key = "3b6770c8a71a4850b2faacbedcb8c0c7"
        self.usd_rub_url = f"https://api.currencyfreaks.com/v2.0/rates/latest?apikey={self.currencyfreaks_api_key}"

    def fetch_usd_rub(self):
        try:
            response = requests.get(self.usd_rub_url)
            data = response.json()
            rate = data["rates"].get("RUB")
            return float(rate) if rate else None
        except Exception as e:
            print(f"❌ Ошибка получения USD/RUB: {e}")
            return None

    def fetch_price(self, market):
        """Получаем цену с Binance для пары CRYPTO/CRYPTO или CRYPTO/USDT"""
        try:
            ticker = self.binance.fetch_ticker(market)
            return ticker["last"]
        except Exception as e:
            print(f"❌ Ошибка получения курса {market}: {e}")
            return None

    def calculate_price(self, row):
        """Рассчитываем price исходя из Market Source и Direction"""
        market = row["Market Source"]
        direction = row["Direction"]

        # FIAT→CRYPTO или CRYPTO→FIAT с USD/RUB
        if market == "USD/RUB":
            usd_rub = self.fetch_usd_rub()
            if usd_rub is None:
                return None
            if direction == "FIAT→CRYPTO":
                return 1 / usd_rub
            else:  # CRYPTO→FIAT
                return usd_rub

        # Остальные пары через Binance
        price = self.fetch_price(market)
        return price

    def update_db(self):
        rows = self.sheet.get_all_records()

        for row in rows:
            price = self.calculate_price(row)
            if price is None:
                continue

            obj = ExchangeRate(
                from_currency=row["From"],
                to_currency=row["To"],
                direction=row["Direction"],
                market_source=row["Market Source"],
                buy_percent=float(row.get("Buy %", 0)),
                sell_percent=float(row.get("Sell %", 0)),
                price=price,
                updated_at=datetime.now(UTC)
            )
            self.sql.add_exchange_rate(obj)
            print(f"✅ Обновлён курс {row['From']} → {row['To']}: {price}")

    def start(self, interval_minutes=30):
        interval = interval_minutes * 60
        while True:
            print(f"\n🔁 Обновление курсов... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.update_db()
            print(f"⏳ Следующее обновление через {interval_minutes} минут")
            time.sleep(interval)


if __name__ == "__main__":
    updater = ExchangeRateUpdater(
        sheet_credentials=r"D:\BUCKET_PROJECT\credentials_for_copies.json",
        sheet_name="test"
    )
    updater.start()
