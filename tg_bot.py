import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppData
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from config import TG_API_KEY, ADMINS

# Инициализация бота
bot = Bot(token=TG_API_KEY, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


# Стартовая команда
@dp.message(F.text == "/start")
async def start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Открыть мини-приложение",
        web_app=WebAppInfo(url="https://oogenetic-factiously-joycelyn.ngrok-free.dev/")
    )
    await message.answer("👋 Привет! Нажми кнопку ниже, чтобы открыть мини-приложение:",
                         reply_markup=builder.as_markup())


# Функция отправки уведомления админам
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


# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
