from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .sql_model import Base, Country, ExchangeRequest, ExchangeRate, TelegramUser


class SQL:
    def __init__(self) -> None:
        # Подключение к PostgreSQL
        URL_DATABASE_LOCAL = "postgresql://postgres:1253@localhost:5432/exchange_bot_DB"

        print("Подключение к локальной базе:")
        print(repr(URL_DATABASE_LOCAL))

        self.engine = create_engine(
            URL_DATABASE_LOCAL,
            connect_args={"client_encoding": "utf8"}
        )

        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    # ---------- БАЗОВЫЕ ОПЕРАЦИИ ----------

    def add_country(self, country: Country) -> None:
        """Добавление новой страны."""
        with self.Session() as session:
            session.add(country)
            session.commit()

    def add_request(self, request: ExchangeRequest) -> None:
        """Добавление заявки."""
        with self.Session() as session:
            session.add(request)
            session.commit()

    def add_exchange_rate(self, obj: ExchangeRate):
        with self.Session() as session:
            session.add(obj)
            session.commit()

    # ---------- ПОЛУЧЕНИЕ ДАННЫХ ----------

    def get_all_countries(self):
        """Получить список всех стран."""
        with self.Session() as session:
            return session.query(Country).all()

    def get_country_by_name(self, name: str):
        """Найти страну по названию."""
        with self.Session() as session:
            stmt = select(Country).where(Country.name == name)
            result = session.execute(stmt).scalar_one_or_none()
            return result

    def get_all_requests(self, limit: int = 50):
        """Получить последние заявки."""
        with self.Session() as session:
            stmt = select(ExchangeRequest).order_by(ExchangeRequest.id.desc()).limit(limit)
            return session.execute(stmt).scalars().all()

    # ---------- СЛУЖЕБНЫЕ МЕТОДЫ ----------

    def seed_countries(self):
        """Синхронизировать таблицу стран с эталонным словарём."""
        with self.Session() as session:
            # Эталонный набор стран
            data = {
                "РОССИЯ": {
                    "code": "RU",
                    "currencies_from_crypto": ["USDT", "BTC"],
                    "currencies_from_fiat": ["RUB", "EUR", "USD"],
                    "cities": ["Москва", "Новосибирск", "Калининград", "Санкт-Петербург",
                               "Сочи", "Казань", "Краснодар"]
                },
                # "США": {
                #     "code": "US",
                #     "currencies_from_crypto": ["USDT", "BTC", "ETH"],
                #     "currencies_from_fiat": ["USD"],
                #     "cities": ["New York", "Los Angeles", "Houston"]
                # },
                # "ПОЛЬША": {
                #     "code": "PL",
                #     "currencies_from_crypto": ["USDT", "ETH"],
                #     "currencies_from_fiat": ["USD", "EUR"],
                #     "cities": ["Варшава", "Белосток", "Плоцк", "Радом"]
                # }
            }

            # Получаем все страны из БД
            existing_countries = {c.name: c for c in session.query(Country).all()}

            # Обновляем или добавляем
            for name, info in data.items():
                if name in existing_countries:
                    country = existing_countries[name]
                    # Проверяем, нужно ли обновлять
                    if (
                            country.code != info["code"] or
                            country.currencies_from_crypto != info["currencies_from_crypto"] or
                            country.currencies_from_fiat != info["currencies_from_fiat"] or
                            country.cities != info["cities"]
                    ):
                        country.code = info["code"]
                        country.currencies_from_crypto = info["currencies_from_crypto"]
                        country.currencies_from_fiat = info["currencies_from_fiat"]
                        country.cities = info["cities"]
                        print(f"🔄 Обновлена страна: {name}")
                else:
                    # Добавляем новую
                    new_country = Country(
                        name=name,
                        code=info["code"],
                        currencies_from_crypto=info["currencies_from_crypto"],
                        currencies_from_fiat=info["currencies_from_fiat"],
                        cities=info["cities"]
                    )
                    session.add(new_country)
                    print(f"➕ Добавлена страна: {name}")

            # Удаляем те, которых нет в словаре
            for name in existing_countries:
                if name not in data:
                    session.delete(existing_countries[name])
                    print(f"❌ Удалена страна: {name}")

            session.commit()
            print("✅ Страны синхронизированы с базой")

    def clear_requests(self):
        """Очистить все заявки"""
        with self.Session() as session:
            deleted = session.query(ExchangeRequest).delete()
            session.commit()
            print(f"Удалено заявок: {deleted}")

    # ------------------- Пользователи -------------------
    def get_user_by_tg_id(self, tg_id: str):
        """Получить пользователя по Telegram ID"""
        with self.Session() as session:
            return session.query(TelegramUser).filter_by(tg_id=str(tg_id)).first()
