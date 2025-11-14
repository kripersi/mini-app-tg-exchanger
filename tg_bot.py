import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

from aiogram.filters import CommandStart
from aiogram.utils.deep_linking import create_start_link, decode_payload

from sqlalchemy import select

from config import TG_API_KEY, ADMINS, URL_SITE
from sql.sql import SQL
from sql.sql_model import Referral

# --- Инициализация ---
bot = Bot(token=TG_API_KEY, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

db = SQL()


async def handle_referral(referrer_id: str, invited_id: str):
    if referrer_id == invited_id:
        return  # нельзя пригласить самого себя

    with db.Session() as session:
        # Уже зарегистрирован?
        exists = session.execute(
            select(Referral).where(Referral.invited_id == str(invited_id))
        ).scalar_one_or_none()

        if exists:
            return

        # Создаём запись
        r = Referral(
            user_id=str(referrer_id),
            invited_id=str(invited_id)
        )
        session.add(r)
        session.commit()

    # Уведомление рефереру
    try:
        await bot.send_message(
            chat_id=referrer_id,
            text=f"🎉 У вас новый реферал!\nПользователь ID: <b>{invited_id}</b>"
        )
    except Exception:
        pass


@dp.message(CommandStart())
async def start_cmd(message: Message):
    text = message.text

    payload = text.replace("/start", "").strip()

    referrer_id = None

    # Если старт по реферальной ссылке
    if payload:
        try:
            referrer_id = decode_payload(payload)
        except:
            referrer_id = None

    invited_id = str(message.from_user.id)

    # Обработка реферала
    if referrer_id:
        await handle_referral(referrer_id, invited_id)

    # Кнопка Mini App
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Открыть мини-приложение",
        web_app=WebAppInfo(url=URL_SITE)
    )

    await message.answer(
        "👋 Привет! Нажми кнопку ниже, чтобы открыть мини-приложение:",
        reply_markup=builder.as_markup()
    )


async def notify_admins(data):
    try:
        user = data.get("user", {})
        text = (
            f"<b>📥 Новая заявка</b>\n\n"
            f"🌍 <b>Страна:</b> {data.get('country')}\n"
            f"🏙️ <b>Город:</b> {data.get('city')}\n"
            f"💱 <b>Обмен:</b> {data.get('give_currency')} → {data.get('get_currency')}\n"
            f"📅 <b>Дата и время:</b> {data.get('datetime')}\n\n"
            f"👤 <b>ФИО:</b> {data.get('fullname')}\n"
            f"📧 <b>Email:</b> {data.get('email')}\n"
            f"🧑‍💻 <b>Telegram:</b> @{user.get('username') or user.get('first_name') or '—'} "
            f"(ID: {user.get('id')})"
        )
        for admin_id in ADMINS:
            await bot.send_message(chat_id=admin_id, text=text)
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение админу: {e}")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
