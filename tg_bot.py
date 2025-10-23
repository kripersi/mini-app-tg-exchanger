from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppData
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from aiogram.client.default import DefaultBotProperties

bot = Bot(token='11111111111111111111',
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


@dp.message(F.text == "/start")
async def start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Открыть мини-приложение",
        web_app=WebAppInfo(url="https://oogenetic-factiously-joycelyn.ngrok-free.dev/")  # тут ngrok для тестов
    )
    await message.answer("Выбери:", reply_markup=builder.as_markup())


@dp.message(F.web_app_data)
async def handle_webapp(message: Message):
    data = message.web_app_data.data
    await message.answer(f"<b>{data}</b>")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
