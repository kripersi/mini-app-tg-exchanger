import asyncio
import logging
import json

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

from aiogram.filters import CommandStart
from aiogram.utils.deep_linking import decode_payload

from config import TG_API_KEY, ADMINS, URL_SITE
from sql.sql import SQL
from sql.sql_model import TelegramUser

#  Инициализация 
bot = Bot(token=TG_API_KEY, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
db = SQL()

# Создаем глобальный event loop для Flask
bot_loop = asyncio.new_event_loop()
asyncio.set_event_loop(bot_loop)


#  Работа с рефералами 
async def handle_referral(referrer_id: str, invited_id: str):
    if str(referrer_id) == str(invited_id):
        return  # нельзя пригласить самого себя

    with db.Session() as session:
        ref_user = session.query(TelegramUser).filter_by(tg_id=str(referrer_id)).first()
        invited_user = session.query(TelegramUser).filter_by(tg_id=str(invited_id)).first()
        if not ref_user or not invited_user:
            return

        referrals = json.loads(ref_user.referrals or '[]')
        if str(invited_id) not in referrals:
            referrals.append(str(invited_id))
            ref_user.referrals = json.dumps(referrals)
            session.commit()

    try:
        await bot.send_message(
            chat_id=referrer_id,
            text=f"🎉 У вас новый реферал!\nПользователь ID: <b>{invited_id}</b>"
        )
    except Exception:
        pass


#  Команда /start 
@dp.message(CommandStart())
async def start_cmd(message: Message):
    payload = message.text.replace("/start", "").strip()
    referrer_id = None
    if payload:
        try:
            referrer_id = decode_payload(payload)
        except Exception:
            referrer_id = None

    invited_id = str(message.from_user.id)
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    try:
        with db.Session() as session:
            user = session.query(TelegramUser).filter_by(tg_id=invited_id).first()
            if not user:
                user = TelegramUser(
                    tg_id=invited_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    referrals=json.dumps([]),
                    referrer_id=str(referrer_id) if referrer_id else None
                )
                session.add(user)
            else:
                if not user.referrer_id and referrer_id and str(referrer_id) != invited_id:
                    user.referrer_id = str(referrer_id)
            session.commit()

        if referrer_id and str(referrer_id) != invited_id:
            await handle_referral(referrer_id, invited_id)

        builder = InlineKeyboardBuilder()
        builder.button(
            text="Открыть мини-приложение",
            web_app=WebAppInfo(url=URL_SITE)
        )

        await message.answer(
            "👋 Привет! Нажми кнопку ниже, чтобы открыть мини-приложение:",
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        import traceback
        logging.error(f"Ошибка в /start: {e}")
        traceback.print_exc()


#  Уведомление админов 
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


#  Функция для Flask 
def notify_admins_sync(data):
    """Вызывается из Flask синхронно"""
    future = asyncio.run_coroutine_threadsafe(notify_admins(data), bot_loop)
    try:
        future.result(timeout=5)
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение админу (sync): {e}")


#  Запуск бота 
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
