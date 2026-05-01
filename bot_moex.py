import sys
import aiohttp
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
        logger.warning(f"New user: {name} (ID: {user.user_id})")

        await event.bot.send_message(
            chat_id=event.chat_id,
            text=f"👋 Привет, {name}!\n\n"
                 "Для запуска бота /start\n\n"
                 "Используйте /help для справки."
        )
    else:
        logger.warning(f"Access denied: {name} (ID: {user.user_id})")

        # 🛑 Нет доступа
        await event.bot.send_message(
            chat_id=event.chat_id,
            text="❌ Доступ запрещён!\n\n"
                 "Этот бот доступен только для авторизованных пользователей.",
        )


async def setup_webhook_subscription():
    """Проверяет и создает webhook-подписку при запуске бота."""
    webhook_url = config('WEBHOOK_URL')
    webhook_secret = config('WEBHOOK_SECRET')
    token = config('MAX_BOT_TOKEN')

    # Данные для создания подписки, как в вашем curl-запросе
    subscription_data = {
        "url": webhook_url,
        "update_types": ["message_created", "bot_started", "message_callback"],
        "secret": webhook_secret
    }

    async with aiohttp.ClientSession() as session:
        # 1. Сначала проверим, есть ли уже активная подписка
        async with session.get(
                "https://platform-api.max.ru/subscriptions",
                headers={"Authorization": token}
        ) as resp:
            if resp.status == 200:
                subscriptions = await resp.json()
                # Если подписка на наш URL уже существует, ничего не делаем
                for sub in subscriptions.get('subscriptions', []):
                    if sub.get('url') == webhook_url:
                        logger.warning("Webhook subscription already exists.")
                        return

        # 2. Если подписки нет, создаем новую
        logger.warning("Creating new webhook subscription...")
        async with session.post(
                "https://platform-api.max.ru/subscriptions",
                headers={"Authorization": token, "Content-Type": "application/json"},
                json=subscription_data
        ) as resp:
            if resp.status == 200:
                logger.warning("Webhook subscription created successfully.")
            else:
                logger.error(f"Failed to create subscription: {await resp.text()}")


async def main():
    logger.warning("Bot is run...")
    # Регистрируем роутер в диспетчере
    dp.include_routers(router)

    if sys.platform == "win32":
        # Для отладки кода под windows
        # Удаляем старую подписку на webhook
        try:
            await bot.delete_webhook()
        except Exception as e:
            logger.warning(f"Error delete webhook: {e}")

        await dp.start_polling(bot)
    elif sys.platform == "linux":
        await setup_webhook_subscription()

        await dp.handle_webhook(
            bot=bot,
            host='127.0.0.1',  # Слушаем только localhost, так как Nginx проксирует запросы
            port=8080,
        )


if __name__ == "__main__":
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    asyncio.run(main())
