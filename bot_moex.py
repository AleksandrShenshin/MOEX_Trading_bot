import sys
import aiohttp
import asyncio
import logging
import basic_handlers
from aiohttp import web
from decouple import config
from basic_handlers import router
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, MessageCreated, MessageCallback

# Объект бота
bot = Bot(token=config('MAX_BOT_TOKEN'))
webhook_secret = config('WEBHOOK_SECRET')
max_user_id = config('MAX_USER_ID')


async def setup_webhook_subscription():
    """Проверяет и создает webhook-подписку при запуске бота."""
    webhook_url = config('WEBHOOK_URL')
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


async def handle_webhook(request):
    """Обрабатывает POST-запросы от MAX."""
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        return web.Response(status=400)

    # Проверка секрета
    received_secret = request.headers.get('X-Max-Bot-Api-Secret')
    if webhook_secret and received_secret != webhook_secret:
        logger.error(f"Invalid secret")
        return web.Response(status=403)

    update_type = data.get('update_type')

    try:
        if update_type == 'message_created':
            event = MessageCreated(**data)
            event.message.bot = bot
            event.bot = bot

            # Прямая обработка команд с вызовом хендлеров
            text = event.message.body.text or ""
            chat_id = event.message.recipient.chat_id
            user_id = event.message.sender.user_id

            # Проверка авторизации
            if str(user_id) != max_user_id:
                await bot.send_message(chat_id=chat_id, text="❌ Доступ запрещён!")
                return web.Response(status=200)

            # Поиск хендлера в роутере
            handler = basic_handlers.get_webhook_handler('message_created', text.split()[0])
            if handler:
                await handler(event)
            else:
                # Для остальных сообщений (FSM, ввод значений)
                from basic_handlers import all_message
                await all_message(event)

            # TODO: del
            # # Обработка команд через ваш роутер
            # elif text.startswith('/del'):
            #     from basic_handlers import del_console
            #     await del_console(event)
            # elif text.startswith('/debug'):
            #     from basic_handlers import debug_console
            #     await debug_console(event)
            # elif text.startswith('/long5'):
            #     from basic_handlers import long5_console
            #     await long5_console(event)
            # else:
            #     # Для остальных сообщений (например, ввод значений для сигналов)
            #     from basic_handlers import all_message
            #     await all_message(event)

        elif update_type == 'bot_started':
            event = BotStarted(**data)
            event.bot = bot
            await basic_handlers.handle_bot_started(event)

        elif update_type == 'message_callback':
            event = MessageCallback(**data)
            event.message.bot = bot
            event.bot = bot

            # Обработка callback-кнопок
            payload = event.callback.payload

            handler = basic_handlers.get_webhook_handler('message_callback', payload)
            if handler:
                await handler(event)
            else:
                logger.warning(f"Unknown callback payload: {payload}")

            # elif payload == 'cmd_add_signal':
            #     from basic_handlers import callback_add_signal
            #     await callback_add_signal(event)
            # elif payload == 'cmd_del_signal':
            #     from basic_handlers import callback_del_signal
            #     await callback_del_signal(event)
            # elif payload.startswith('typesignal_'):
            #     from basic_handlers import handle_set_type_signal
            #     await handle_set_type_signal(event)
            # elif payload.startswith('ticker_'):
            #     from basic_handlers import handle_set_ticker
            #     await handle_set_ticker(event)
            # elif payload == 'cancel_signal':
            #     from basic_handlers import handle_cancel_signal
            #     await handle_cancel_signal(event)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

    return web.Response(status=200)


async def main():
    logger.warning("Bot is run...")

    if sys.platform == "win32":
        # Для отладки кода под windows
        logger.warning("Running on Windows: using LONG POLLING mode")

        # Диспетчер
        dp = Dispatcher()

        # Регистрируем роутер в диспетчере
        dp.include_routers(router)

        # Удаляем старую подписку на webhook
        try:
            await bot.delete_webhook()
        except Exception as e:
            logger.warning(f"Error delete webhook: {e}")

        await dp.start_polling(bot)
    elif sys.platform == "linux":
        logger.warning("Running on Linux: using WEBHOOK mode")

        await setup_webhook_subscription()

        app = web.Application()
        app.router.add_post('/webhook', handle_webhook)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', 8080)
        await site.start()

        logger.warning("Webhook server running on http://127.0.0.1:8080")
        await asyncio.Event().wait()


if __name__ == "__main__":
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    asyncio.run(main())
