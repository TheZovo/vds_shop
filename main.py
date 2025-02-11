import asyncio
from aiogram import Bot, Dispatcher
from functions.functions import create_db
from config import config
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties 
from handlers.handlers import router


async def main():
    create_db()
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
