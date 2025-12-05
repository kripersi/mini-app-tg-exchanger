import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .sql_model import Base, Country, ExchangeRequest, ExchangeRate, TelegramUser


class SQL:
    def __init__(self) -> None:
        # Подключение к PostgreSQL через переменную окружения или локально
        URL_DATABASE = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:1253@localhost:5432/exchange_bot_DB"
        )

        print("Подключение к базе:")
        print(repr(URL_DATABASE))

        self.engine = create_engine(
            URL_DATABASE,
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
        """Добавление курса."""
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
            return session.execute(stmt).scalar_one_or_none()

    def get_all_requests(self, limit: int = 50):
        """Получить последние заявки."""
        with self.Session() as session:
            stmt = select(ExchangeRequest).order_by(ExchangeRequest.id.desc()).limit(limit)
            return session.execute(stmt).scalars().all()

    # ---------- СЛУЖЕБНЫЕ МЕТОДЫ ----------

    def clear_requests(self):
        """Очистить все заявки."""
        with self.Session() as session:
            deleted = session.query(ExchangeRequest).delete()
            session.commit()
            print(f"Удалено заявок: {deleted}")

    # ---------- ПОЛЬЗОВАТЕЛИ ----------

    def get_user_by_tg_id(self, tg_id: str):
        """Получить пользователя по Telegram ID."""
        with self.Session() as session:
            return session.query(TelegramUser).filter_by(tg_id=str(tg_id)).first()
