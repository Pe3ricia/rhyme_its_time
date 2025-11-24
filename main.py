import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

# Загружаем .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Токен не найден! Проверь файл .env")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# Импортируем роутеры (убедись, что папка handlers существует и содержит файлы)
from handlers.start import router as start_router
from handlers.registration import router as registration_router

# Подключаем роутеры
dp.include_router(start_router)
dp.include_router(registration_router)

# Функция для установки команд меню (опционально, но удобно)
async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Начать или обновить профиль"),
        BotCommand(command="/newgame", description="Создать новую игру"),
        BotCommand(command="/join", description="Присоединиться к игре"),
    ]
    await bot.set_my_commands(commands)

# Инициализация БД
from database.engine import engine
from database.models import Base

async def on_startup():
    # Создаём таблицы, если их нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await set_bot_commands()

async def main() -> None:
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())