import requests
import ccxt
from datetime import datetime, timezone
from sql.sql import SQL
from sql.sql_model import ExchangeRate
from utils.google_sheet import GoogleSheet
import time
from config import CURRENCY_API_FOR_USD, SHEET_NAME, CREDENTIALS_SHEET


class ExchangeRateUpdater:
    def __init__(self, sheet_credentials, sheet_name):
        self.sheet = GoogleSheet(sheet_credentials, sheet_name)
        self.sql = SQL()
        self.binance = ccxt.binance()
        self.usd_rub_url = f"https://api.currencyfreaks.com/v2.0/rates/latest?apikey={CURRENCY_API_FOR_USD}"

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

    def get_price(self, market_source, direction):
        """Рассчитываем актуальную цену"""
        if market_source.upper() == "USDT/RUB":
            usd_rub = self.fetch_usd_rub()
            if usd_rub is None:
                return None
            return 1 / usd_rub if direction == "FIAT→CRYPTO" else usd_rub

        # Для остальных пар (например BTC/USDT, ETH/RUB)
        return self.fetch_price(market_source)

    def update_db(self):
        rows = self.sheet.get_all_records()

        for row in rows:
            price = self.get_price(row["Market Source"], row["Direction"])
            if price is None:
                print(f"❌ Не удалось получить цену для {row['From']} → {row['To']}")
                continue

            obj = ExchangeRate(
                from_currency=row["From"],
                to_currency=row["To"],
                market_source=row["Market Source"],
                direction=row["Direction"],
                buy_percent=float(row.get("Buy %", 0)),
                sell_percent=float(row.get("Sell %", 0)),
                buy_rate_formul=row.get("Buy Rate formul", ""),
                sell_rate_formul=row.get("Sell Rate formul", ""),
                price=price,
                updated_at=datetime.now(timezone.utc)
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
        sheet_credentials=CREDENTIALS_SHEET,
        sheet_name=SHEET_NAME
    )
    updater.start()
