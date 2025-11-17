from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ---------- 1. Таблица стран и данных о доступных валютах ----------
class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # Пример: "США"
    code = Column(String(5), nullable=False)  # Пример: "US"
    currencies_from_crypto = Column(JSON, nullable=False)  # ["USDT", "BTC", "ETH"]
    currencies_from_fiat = Column(JSON, nullable=False)  # ["USD"]
    cities = Column(JSON, nullable=False)  # ["New York", "Los Angeles", ...]

    # Связь с заявками
    requests = relationship(
        "ExchangeRequest",
        back_populates="country_data",
        cascade="all, delete-orphan"
    )


# ---------- 2. Таблица заявок пользователей ----------
class ExchangeRequest(Base):
    __tablename__ = "exchange_requests"

    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)

    give_currency = Column(String, nullable=False)
    get_currency = Column(String, nullable=False)
    give_amount = Column(Float, nullable=False)  # сколько отдаёт
    get_amount = Column(Float, nullable=False)  # сколько получает

    city = Column(String, nullable=False)
    fullname = Column(String, nullable=False)
    email = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Информация о пользователе Telegram
    user_id = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)

    # статус сделки
    status = Column(String, nullable=False, default="открыта")  # открыта, отменена, выполнена

    country_data = relationship("Country", back_populates="requests")


# ---------- 3. Таблица курса ----------
class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pair = Column(String, nullable=False)  # например "RUB/USDT"
    rate = Column(Float, nullable=False)   # курс (например 83.5124)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ---------- 4. Пользователи ----------
class TelegramUser(Base):
    __tablename__ = "users_bot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(String, unique=True, nullable=False)  # ID Telegram
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    banned = Column(Boolean, default=False)  # True / False
    first_start = Column(DateTime, default=datetime.utcnow)
    email = Column(String, nullable=True)

    referrals = Column(JSON, default=[])  # список tg_id приглашённых
    referrer_id = Column(String, nullable=True)  # tg_id того, кто пригласил

