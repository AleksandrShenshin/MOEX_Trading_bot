import os
import asyncio
import logging

from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, BotStarted, Command

# from aiogram import Bot, Dispatcher, types
# from aiogram.enums import ParseMode
# from aiogram.filters.command import Command
from basic_handlers import router
# from aiogram.utils.keyboard import ReplyKeyboardBuilder
# from aiogram.client.default import DefaultBotProperties
# from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.context import FSMContext
# from general import moex_infinite_loop, set_user_id, update_current_ticker
# from general import lock_state
from decouple import config
import journal

# Объект бота
#bot = Bot(token=config('MAX_BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot = Bot(token=config('MAX_BOT_TOKEN'))

# Диспетчер
#dp = Dispatcher(storage=MemoryStorage())
dp = Dispatcher()

# TODO: добавить автоматический поиск прострелов


# @dp.message_created(F.message.body.text)
# async def echo(event: MessageCreated):
#     await event.message.answer(f"Повторяю за вами: {event.message.body.text}")


# # Обработчик нажатия кнопки "Начать" (первый запуск)
# @dp.bot_started()
# async def handle_bot_started(event: BotStarted):
#     """Вызывается когда пользователь нажимает 'Начать'"""
#     user = event.user
#     name = getattr(user, 'first_name', None) or 'друг'
#
#     logger.info(f"New user: {name} (ID: {user.user_id})")
#
#     await bot.send_message(
#         chat_id=event.chat_id,
#         text=f"👋 Привет, {name}!\n\n"
#              "Я ваш помощник. Чем могу помочь?\n\n"
#              "Используйте /help для справки."
#     )


# Хэндлер на команду /start
@dp.message_created(Command("start"))
# async def cmd_start(message: types.Message, state: FSMContext):
async def cmd_start(event: MessageCreated):
#     stat_init = ''
#     lock_state.acquire()
#     await state.clear()
#     await state.update_data(bot=bot)
#     await state.update_data(debug=None)
#     lock_state.release()
#
#     await set_user_id(message.from_user.id)
#
#     ret_val, err_msg = await update_current_ticker(state)
#     if ret_val:
#         await message.answer(f"❌ <b>ОШИБКА:</b> {err_msg}")
#         os._exit(-1)
#     else:
#         stat_init = "✅ Получение тикеров"
#         msg = await message.answer(stat_init)
#
#     data = await journal.get_signals_from_file()
#     lock_state.acquire()
#     await state.update_data(signals=data)
#     lock_state.release()
#
#     stat_init = f"{stat_init}\n✅ Получение сигналов"
#     await message.bot.edit_message_text(stat_init, chat_id=message.from_user.id, message_id=msg.message_id)
#
#     # Start the infinite loop as a background task
#     asyncio.create_task(moex_infinite_loop(state))
#
#     # Создаем объект билдера для Reply-клавиатуры
#     builder = ReplyKeyboardBuilder()
#
#     # Добавляем кнопки
#     builder.button(text="📋 Просмотр сигналов")
#     builder.button(text="➕ Добавить сигнал")
#     builder.button(text="💡 README")
#     builder.button(text="➖ Удалить сигнал")
#
#     # Указываем, сколько кнопок будет в одном ряду (в данном случае 2 в первом ряду и две во втором ряду)
#     builder.adjust(2, 2)
#
#     await message.answer(
#         "<b>MOEX Trading Bot is running</b>",
#         reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
#     )

    await event.message.answer(
        f"👋 Привет!\n\n"
        "Добро пожаловать! Я готов помочь."
    )


# Запуск процесса поллинга новых апдейтов
async def main():
    logger.info("Bot is run...")
    # Регистрируем роутер в диспетчере
    dp.include_routers(router)
    
#    # Удаляем webhook для режима polling
#    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await bot.delete_webhook()
    except Exception as e:
        logger.warning(f"Error delete webhook: {e}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    asyncio.run(main())
