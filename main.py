import os
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
from general import moex_infinite_loop, set_user_id, update_current_ticker
from general import lock_state
from decouple import config
import journal

# Объект бота
bot = Bot(token=config('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Диспетчер
dp = Dispatcher(storage=MemoryStorage())

# TODO: добавить автоматический поиск прострелов


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    stat_init = ''
    lock_state.acquire()
    await state.clear()
    await state.update_data(bot=bot)
    await state.update_data(debug=None)
    lock_state.release()

    await set_user_id(message.from_user.id)

    ret_val, err_msg = await update_current_ticker(state)
    if ret_val:
        await message.answer(f"❌ <b>ОШИБКА:</b> {err_msg}")
        os._exit(-1)
    else:
        stat_init = "✅ Получение тикеров"
        msg = await message.answer(stat_init)

    data = await journal.get_signals_from_file()
    lock_state.acquire()
    await state.update_data(signals=data)
    lock_state.release()

    stat_init = f"{stat_init}\n✅ Получение сигналов"
    await message.bot.edit_message_text(stat_init, chat_id=message.from_user.id, message_id=msg.message_id)

    # Start the infinite loop as a background task
    asyncio.create_task(moex_infinite_loop(state))

    # Создаем объект билдера для Reply-клавиатуры
    builder = ReplyKeyboardBuilder()

    # Добавляем кнопки
    builder.button(text="📋 Просмотр сигналов")
    builder.button(text="➕ Добавить сигнал")
    builder.button(text="💡 README")
    builder.button(text="➖ Удалить сигнал")

    # Указываем, сколько кнопок будет в одном ряду (в данном случае 2 в первом ряду и две во втором ряду)
    builder.adjust(2, 2)

    await message.answer(
        "<b>MOEX Trading Bot is running</b>",
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )


# Запуск процесса поллинга новых апдейтов
async def main():
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
