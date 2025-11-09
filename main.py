import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command
from basic_handlers import router
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from decouple import config

USER_ID = None

# Объект бота
bot = Bot(token=config('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Диспетчер
dp = Dispatcher(storage=MemoryStorage())


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    global USER_ID

    await state.clear()
#    await state.update_data(user_id=message.from_user.id)

    # Создаем объект билдера для Reply-клавиатуры
    builder = ReplyKeyboardBuilder()

    # Добавляем кнопки
    builder.button(text="Просмотр сигналов")
    builder.button(text="Добавить сигнал")
    builder.button(text="/help")

    # Указываем, сколько кнопок будет в одном ряду (в данном случае 2 в первом ряду и одна во втором ряду)
    builder.adjust(2, 1)

    await message.answer(
        "<b>MOEX Trading Bot is running</b>",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    asyncio.run(main())
