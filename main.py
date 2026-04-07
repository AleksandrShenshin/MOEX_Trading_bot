import asyncio
import logging
from decouple import config
from basic_handlers import router
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted

# Объект бота
bot = Bot(token=config('MAX_BOT_TOKEN'))

# Диспетчер
dp = Dispatcher()


# Обработчик нажатия кнопки "Начать" (первый запуск)
@dp.bot_started()
async def handle_bot_started(event: BotStarted):
    """Вызывается когда пользователь нажимает 'Начать'"""
    user = event.user
    name = getattr(user, 'first_name', None) or 'friend'

    if str(user.user_id) == config('MAX_USER_ID'):
        logger.info(f"New user: {name} (ID: {user.user_id})")

        await event.bot.send_message(
            chat_id=event.chat_id,
            text=f"👋 Привет, {name}!\n\n"
                 "Для запуска бота /start\n\n"
                 "Используйте /help для справки."
        )
    else:
        logger.info(f"Access denied: {name} (ID: {user.user_id})")

        # 🛑 Нет доступа
        await event.bot.send_message(
            chat_id=event.chat_id,
            text="❌ Доступ запрещён!\n\n"
                 "Этот бот доступен только для авторизованных пользователей.",
        )


# Запуск процесса поллинга новых апдейтов
async def main():
    logger.info("Bot is run...")
    # Регистрируем роутер в диспетчере
    dp.include_routers(router)
    
    # Удаляем webhook для режима polling
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
