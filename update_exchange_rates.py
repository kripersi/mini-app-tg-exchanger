import requests
import ccxt
from datetime import datetime, timezone
from sql.sql import SQL
from sql.sql_model import ExchangeRate, Country
from utils.google_sheet import GoogleSheet
import time
from config import CURRENCY_API_FOR_USD, SHEET_NAME, CREDENTIALS_SHEET, TAB_EXCHANGE, TAB_COUNTRY_NAME


class ExchangeRateUpdater:
    def __init__(self, sheet_credentials, sheet_name):
        # Лист курсов
        self.sheet_rates = GoogleSheet(
            credentials_path=sheet_credentials,
            sheet_name=sheet_name,
            tab_name=TAB_EXCHANGE
        )

        # Лист стран
        self.sheet_countries = GoogleSheet(
            credentials_path=sheet_credentials,
            sheet_name=sheet_name,
            tab_name=TAB_COUNTRY_NAME
        )

        self.sql = SQL()
        self.binance = ccxt.binance()
        self.usd_rub_url = f"https://api.currencyfreaks.com/v2.0/rates/latest?apikey={CURRENCY_API_FOR_USD}"

    # ---------------- COUNTRY SYNC ----------------
    def update_countries(self):
        rows = self.sheet_countries.get_all_records()
        session = self.sql.Session()

        existing = {c.name: c for c in session.query(Country).all()}
        new_names = set()

        for row in rows:
            name = row["Страна"].strip()
            new_names.add(name)

            code = row["Код"].strip()
            crypto = [x.strip() for x in row["Криптовалюты"].split(",")]
            fiat = [x.strip() for x in row["Фиатные валюты"].split(",")]
            cities = [x.strip() for x in row["Города"].split(",")]

            if name in existing:
                c = existing[name]
                c.code = code
                c.currencies_from_crypto = crypto
                c.currencies_from_fiat = fiat
                c.cities = cities
                print(f"🔄 Обновлена страна: {name}")
            else:
                session.add(
                    Country(
                        name=name,
                        code=code,
                        currencies_from_crypto=crypto,
                        currencies_from_fiat=fiat,
                        cities=cities
                    )
                )
                print(f"➕ Добавлена страна: {name}")

        for name in existing:
            if name not in new_names:
                session.delete(existing[name])
                print(f"❌ Удалена страна: {name}")

        session.commit()
        session.close()
        print("✅ Страны синхронизированы")

    # ---------------- EXCHANGE RATES ----------------
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
        try:
            ticker = self.binance.fetch_ticker(market)
            return ticker["last"]
        except Exception as e:
            print(f"❌ Ошибка получения курса {market}: {e}")
            return None

    def get_price(self, market_source, direction):
        if market_source.upper() == "USDT/RUB":
            usd_rub = self.fetch_usd_rub()
            if usd_rub is None:
                return None
            return 1 / usd_rub if direction == "FIAT→CRYPTO" else usd_rub

        return self.fetch_price(market_source)

    def update_db(self):
        rows = self.sheet_rates.get_all_records()

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

    # ---------------- MAIN LOOP ----------------
    def start(self, interval_minutes=30):
        interval = interval_minutes * 60

        while True:
            print("\n🔁 Обновление данных...")

            self.update_countries()
            self.update_db()

            print(f"⏳ Следующее обновление через {interval_minutes} минут")
            time.sleep(interval)


if __name__ == "__main__":
    updater = ExchangeRateUpdater(
        sheet_credentials=CREDENTIALS_SHEET,
        sheet_name=SHEET_NAME
    )
    updater.start()
