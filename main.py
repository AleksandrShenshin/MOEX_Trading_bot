import asyncio
import logging

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters.command import Command

# ВАЖНО! Вставьте сюда ваш токен, полученный от @BotFather
BOT_TOKEN = ''

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()

# Создаем экземпляр роутера
router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Я умею делать следующее...")

# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я эхо-бот. Отправь мне любое сообщение, и я его повторю.")

# Хэндлер на остальные текстовые сообщения
@router.message()
async def echo_message(message: types.Message):
    await message.answer(f"Я получил твое сообщение: {message.text}")

# Запуск процесса поллинга новых апдейтов
async def main():
    # Регистрируем роутер в диспетчере
    dp.include_router(router)
    
    # Удаляем вебхук и пропускаем накопившиеся входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())