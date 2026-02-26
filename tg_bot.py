import asyncio
import logging
import json
import requests

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
from extensions import bot_loop

# Инициализация бота
bot = Bot(token=TG_API_KEY, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
db = SQL()

# Установка глобального event loop
asyncio.set_event_loop(bot_loop)


# Работа с рефералами
async def handle_referral(referrer_id: str, invited_id: str):
    if str(referrer_id) == str(invited_id):
        return

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


# /start
@dp.message(CommandStart())
async def start_cmd(message: Message):
    payload = message.text.replace("/start", "").strip()
    referrer_id = payload if payload.isdigit() else None

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
            "Добро пожаловать в крипто-обменный бот MonettiX 🔐 \n"
            "Нажмите кнопку ниже, чтобы открыть мини-приложение",
            reply_markup=builder.as_markup()
        )

    except Exception as e:
        logging.error(f"Ошибка в /start: {e}")


# Уведомление админов
def notify_admins(data):
    try:
        try:
            give_amount = float(str(data.get("give_amount")).replace(",", "."))
            get_amount = float(str(data.get("get_amount")).replace(",", "."))
            rate = get_amount / give_amount if give_amount else 0
            rate = round(rate, 4)
        except Exception:
            rate = "—"

        user = data.get("user", {})
        tg_url = f"https://api.telegram.org/bot{TG_API_KEY}/sendMessage"
        text = (
            f"<b>📥 Новая заявка</b>\n\n"
            f"🌍 <b>Страна:</b> {data.get('country')}\n"
            f"🏙️ <b>Город:</b> {data.get('city')}\n"
            f"💱 <b>Обмен:</b> {data.get('give_currency')} → {data.get('get_currency')}\n"
            f"💰 <b>Отдаёт:</b> {data.get('give_amount')} {data.get('give_currency')}\n"
            f"💵 <b>Получает:</b> {data.get('get_amount')} {data.get('get_currency')}\n"
            f"📊 <b>Курс за {data.get('give_currency')}:</b> {rate} {data.get('get_currency')}\n\n"
            f"📅 <b>Дата и время:</b> {data.get('datetime')}\n\n"
            f"👤 <b>ФИО:</b> {data.get('fullname')}\n"
            f"📧 <b>Email:</b> {data.get('email')}\n"
            f"🧑‍💻 <b>Telegram:</b> @{user.get('username') or user.get('first_name') or '—'} "
            f"(ID: {user.get('id')})"
        )

        for admin_id in ADMINS:
            try:
                requests.post(
                    tg_url,
                    data={"chat_id": admin_id, "text": text, "parse_mode": "HTML"},
                    timeout=15
                )
            except Exception as e:
                logging.error(f"Ошибка отправки в Telegram: {e}")
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение админу: {e}")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    bot_loop.create_task(main())
    bot_loop.run_forever()
