import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from handlers.basic_handlers import router
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BOT_TOKEN = ''
USER_ID = None

# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    global USER_ID

    # Создаем объект билдера для Reply-клавиатуры
    builder = ReplyKeyboardBuilder()

    # Добавляем кнопки
    builder.button(text="Просмотр сигналов")
    builder.button(text="Добавить сигнал")
    builder.button(text="/help")

    # Указываем, сколько кнопок будет в одном ряду (в данном случае 2)
    builder.adjust(2)

    await message.answer(
        "<b>MOEX Trading Bot is running</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    USER_ID = message.from_user.id


# Define your infinite loop function
async def moex_infinite_loop():
    global USER_ID

    while True:
        if USER_ID is not None:
            print("Infinite loop is running...", flush=True)
            await bot.send_message(USER_ID, "Infinite loop is running...")
            # Add your desired logic here
        await asyncio.sleep(5)  # Sleep for 5 seconds to avoid busy-waiting


# Запуск процесса поллинга новых апдейтов
async def main():
    # Start the infinite loop as a background task
    asyncio.create_task(moex_infinite_loop())

    # Регистрируем роутер в диспетчере
    dp.include_router(router)
    
    # Удаляем вебхук и пропускаем накопившиеся входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
