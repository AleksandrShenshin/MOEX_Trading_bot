import os
import asyncio
import journal
import t_invest_lib.tinv as tinv
import logging
from decouple import config
from maxapi import F, Router
from maxapi.types import MessageCreated, MessageCallback, Command, CallbackButton, ButtonsPayload, Attachment
from maxapi.enums.intent import Intent
from general import get_support_instruments, get_support_signals, get_precision_from_value, update_current_ticker, moex_infinite_loop
from general import lock_state, storage
from fsm_memory import FSMContextLike

logger = logging.getLogger(__name__)

# Все роутеры нужно именовать так, чтобы не было конфликтов
router = Router()


def create_main_menu():
    """Создаёт главное меню с кнопками"""

    # Создаём кнопки
    btn_get_list_signal = CallbackButton(
        text="📋 Просмотр сигналов",
        payload="cmd_get_list_signal",
        intent=Intent.DEFAULT
    )

    btn_add_signal = CallbackButton(
        text="➕ Добавить сигнал",
        payload="cmd_add_signal",
        intent=Intent.DEFAULT
    )

    btn_help = CallbackButton(
        text="💡 README",
        payload="cmd_help",
        intent=Intent.POSITIVE
    )

    btn_del_signal = CallbackButton(
        text="➖ Удалить сигнал",
        payload="cmd_del_signal",
        intent=Intent.POSITIVE
    )

    # Группируем кнопки в ряды
    # Каждый вложенный список — отдельный ряд
    buttons_payload = ButtonsPayload(
        buttons=[
            [btn_get_list_signal, btn_add_signal],  # Первый ряд: 2 кнопки
            [btn_help, btn_del_signal]              # Второй ряд: 1 кнопка
        ]
    )

    # Создаём attachment для отправки
    return Attachment(type="inline_keyboard", payload=buttons_payload)


# TODO: добавить stop команду
# Хэндлер на команду /start
@router.message_created(Command("start"))
async def cmd_start(event: MessageCreated):
    user_id = event.from_user.user_id
    state = FSMContextLike(storage, user_id)
    if str(user_id) != config('MAX_USER_ID'):
        await event.message.answer(
            "❌ Доступ запрещён!\n\n"
               "Этот бот доступен только для авторизованных пользователей.",
        )
        return
    else:
        await event.message.answer(f"👋 Привет, инициализация...")

    stat_init = ''
    lock_state.acquire()
    await state.clear()
    await state.update_data(bot=event.bot)
    await state.update_data(chat_id=event.chat.chat_id)
    await state.update_data(debug=None)
    lock_state.release()

    try:
        ret_val, err_msg = await update_current_ticker(state)
        if ret_val:
            await event.message.answer(f"❌ ОШИБКА: {err_msg}\n\nBot: Process finished with exit code -1")
            os._exit(-1)
        else:
            stat_init = "✅ Получение тикеров"
            msg = await event.message.answer(stat_init)

        data = await journal.get_signals_from_file()
        lock_state.acquire()
        await state.update_data(signals=data)
        lock_state.release()

        stat_init = f"{stat_init}\n✅ Получение сигналов"
        await event.bot.edit_message(message_id=msg.message.body.mid, text=stat_init)
    except Exception as e:
        logger.error(f"Command('start'): ERROR: {type(e).__name__}: {e}")
        await event.message.answer(f"❌ ОШИБКА: {type(e).__name__}: {e}\n\nBot: Process finished with exit code -1")
        os._exit(-1)

    # Start the infinite loop as a background task
    asyncio.create_task(moex_infinite_loop(state))

    menu_buttons = create_main_menu()
    await event.message.answer("MOEX Trading Bot is running", attachments=[menu_buttons])


@router.message_created(Command('menu'))
async def cmd_menu(event: MessageCreated):
    """Показать главное меню"""

    menu_buttons = create_main_menu()

    await event.message.answer("🏠 Главное меню", attachments=[menu_buttons])


@router.message_created(Command("help"))
@router.message_callback(F.callback.payload == "cmd_help")
async def cmd_help(event: MessageCreated):
    readme_message = "Поддерживаемые команды:\n"
    fl_wr_line = False

    try:
        with open('README.md', "r", encoding="utf-8") as file:
            for line in file:
                if fl_wr_line:
                    if '<<<<<' in line:
                        break
                    else:
                        readme_message += line
                elif '>>>>>' in line:
                    fl_wr_line = True
    except FileNotFoundError:
        pass
    finally:
        await event.message.answer(readme_message)


@router.message_created(Command("get_list_ticker"))
async def get_support_ticker(event: MessageCreated):
    support_ticker = ""
    supp_instr = await get_support_instruments()
    for text_ticker in supp_instr:
        if not support_ticker:
            support_ticker += text_ticker.lower()
        else:
            support_ticker += f", {text_ticker.lower()}"
    await event.message.answer(support_ticker)


@router.message_created(Command("get_signals"))
@router.message_callback(F.callback.payload == "cmd_get_list_signal")
async def get_list_signal(event: MessageCreated):
    user_id = event.from_user.user_id
    state = FSMContextLike(storage, user_id)

    lock_state.acquire()
    all_data = await state.get_data()
    try:
        data = all_data['signals']
    except KeyError:
        data = {}
    lock_state.release()

    if len(data) != 0:
        msg_to_print = f"Активные сигналы:\n"

        list_signals = []
        for key, value in data.items():
            if value['type_signal'].lower() == 'long5' or value['type_signal'].lower() == 'throws':
                continue
            curr_signal = value.copy()
            curr_signal['id'] = key
            curr_signal['value'] = float(value['value'])
            list_signals.append(curr_signal)

        # Сортировка по value
        list_signals = sorted(list_signals, key=lambda d: d['value'], reverse=True)
        # Сортировка по type_signal
        list_signals = sorted(list_signals, key=lambda d: d['type_signal'])
        # Сортировка по ticker
        list_signals = sorted(list_signals, key=lambda d: d['ticker'])

        try:
            for signal in list_signals:
                msg_to_print += f"{signal['id']}: {signal['ticker']} {signal['type_signal']} {data[signal['id']]['value']}\n"
            for key, value in data.items():
                if value['type_signal'].lower() == 'long5' or value['type_signal'].lower() == 'throws':
                    msg_to_print += f"{key}: {value['type_signal']} {value['market']}\n"
            await event.message.answer(msg_to_print)
        except KeyError:
            await event.message.answer("❌ ОШИБКА: получения данных")
    else:
        await event.message.answer(f"Нет активных сигналов")


@router.message_created(Command("set"))
async def set_console(event: MessageCreated):
    state = FSMContextLike(storage, event.from_user.user_id)

    full_text = (event.message.body.text or "").strip()
    parts = full_text.split(maxsplit=1)
    command_args = parts[1] if len(parts) > 1 else ""
    if not command_args or len(command_args.split()) != 3:
        await event.message.answer(f"❌ Использование: /set TICKER TYPE_SIGNAL VALUE")
        return

    ticker, param_signal, value = command_args.split()

    supp_signals = await get_support_signals()
    for text_signal, param_val in supp_signals.items():
        try:
            if param_signal != param_val['param']:
                continue
        except KeyError as e:
            await event.message.answer(f"❌ ERROR: set_console(): KeyError {e}")
            break
        else:
            await add_signal(event.message, state, ticker, text_signal, value)
            break
    else:
        await event.message.answer(f"❌ ERROR: параметр {param_signal} не корректный.")


async def state_clear_soft(state):
    lock_state.acquire()
    data = await state.get_data()
    try:
        supp_tools = data['supp_tools']
    except KeyError:
        supp_tools = {}

    try:
        signals = data['signals']
    except KeyError:
        signals = {}

    try:
        chat_id = data['chat_id']
    except KeyError:
        chat_id = None

    try:
        debug = data['debug']
    except KeyError:
        debug = None

    try:
        bot = data['bot']
    except KeyError:
        bot = None

    await state.clear()
    await state.update_data(supp_tools=supp_tools)
    await state.update_data(signals=signals)
    await state.update_data(chat_id=chat_id)
    await state.update_data(debug=debug)
    await state.update_data(bot=bot)
    lock_state.release()


@router.message_callback(F.callback.payload == "cmd_add_signal")
async def callback_add_signal(event: MessageCallback):
    user_id = event.from_user.user_id
    state = FSMContextLike(storage, user_id)

    await state_clear_soft(state)

    # Собираем кнопки: 2 в ряд, как builder.adjust(2)
    buttons: list[list[dict]] = []
    row: list[dict] = []

    supp_signals = await get_support_signals()
    for text_signal, param_signal in supp_signals.items():
        row.append({
            "type": "callback",
            "text": text_signal,
            "payload": f"typesignal_{text_signal.lower()}",
        })
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    keyboard_attachment = Attachment(
        type="inline_keyboard",
        payload={"buttons": buttons},
    )

    await event.message.answer(
        "Выберите тип сигнала:",
        attachments=[keyboard_attachment],
    )


@router.message_callback(F.callback.payload.startswith("typesignal_"))
async def handle_set_type_signal(event: MessageCallback):
    user_id = event.from_user.user_id
    state = FSMContextLike(storage, user_id)

    type_signal = event.callback.payload.split("_", 1)[1]

    lock_state.acquire()
    await state.update_data(type_signal=type_signal)
    data = await state.get_data()
    lock_state.release()

    buttons: list[list[dict]] = []
    row: list[dict] = []

    if type_signal == "long5" or type_signal == "throws":
        for market in ["forts", "moex"]:
            row.append({
                "type": "callback",
                "text": market,
                "payload": f"ticker_{market}",
            })
            if len(row) == 3:
                buttons.append(row)
                row = []
    else:
        for short_ticker, val_short_ticker in data["supp_tools"].items():
            text_ticker = val_short_ticker["current_ticker"]
            row.append({
                "type": "callback",
                "text": text_ticker,
                "payload": f"ticker_{text_ticker}",
            })
            if len(row) == 3:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)

    keyboard_attachment = Attachment(
        type="inline_keyboard",
        payload={"buttons": buttons},
    )

    # Редактируем текст исходного сообщения
    mid = event.message.body.mid

    if type_signal == "long5" or type_signal == "throws":
        new_text = "Выберите рынок:"
    else:
        new_text = "Выберите инструмент:"

    await event.bot.edit_message(
        message_id=mid,
        text=new_text,
        attachments=[keyboard_attachment],
    )


@router.message_callback(F.callback.payload.startswith("ticker_"))
async def handle_set_ticker(event: MessageCallback):
    state = FSMContextLike(storage, event.from_user.user_id)

    ticker = event.callback.payload.split("_", 1)[1]

    if ticker in ["forts", "moex"]:
        # удалить сообщение с кнопками
        mid = event.message.body.mid
        await event.bot.delete_message(message_id=mid)

        lock_state.acquire()
        all_data = await state.get_data()
        lock_state.release()

        await state_clear_soft(state)

        try:
            for key, value in all_data["signals"].items():
                if (value["type_signal"].lower() == all_data["type_signal"] and value["market"] == ticker):
                    await event.message.answer(f"📝 ✅ {value['type_signal'].lower()} {value['market']} уже установлен!")
                    return
        except KeyError:
            await event.message.answer("❌ ERROR: handle_set_ticker(): format state")
        else:
            await add_signal(event.message, state, ticker, all_data["type_signal"], None)
    else:
        lock_state.acquire()
        await state.update_data(ticker=ticker)
        await state.update_data(msg_id_for_del=event.message.body.mid)
        data = await state.get_data()
        lock_state.release()

        # Кнопка "Отмена"
        buttons = [[
            {
                "type": "callback",
                "text": "Отмена",
                "payload": "cancel_signal",
            }
        ]]
        keyboard_attachment = Attachment(
            type="inline_keyboard",
            payload={"buttons": buttons},
        )

        # Редактируем текст исходного сообщения: "Введите значение <TICKER> <TYPE_SIGNAL>"
        mid = event.message.body.mid
        new_text = f"Введите значение {data['ticker']} {data['type_signal']}:"

        await event.bot.edit_message(
            message_id=mid,
            text=new_text,
            attachments=[keyboard_attachment],
        )

        lock_state.acquire()
        await state.set_state("Form.value")
        lock_state.release()


@router.message_callback(F.callback.payload == "cancel_signal")
async def handle_cancel_signal(event: MessageCallback):
    state = FSMContextLike(storage, event.from_user.user_id)
    await event.bot.delete_message(message_id=event.message.body.mid)
    await state_clear_soft(state)


async def add_signal(message, state, ticker, type_signal, value):
    supp_signals = await get_support_signals()
    for text_signal, param_signal in supp_signals.items():
        if text_signal.lower() == type_signal.lower():
            break
    else:
        await message.answer(f"❌ ERROR: тип сигнала {type_signal} не корректный")
        return

    if type_signal.lower() == 'volume':
        try:
            int(value)
        except ValueError:
            await message.answer(f"❌ ERROR: значение {value} должно быть целым для {type_signal}")
            return
    elif type_signal.lower() == 'price':
        value = value.replace(',', '.')
        try:
            float(value)
        except ValueError:
            await message.answer(f"❌ ERROR: значение {value} должно содержать только цифры")
            return

    if type_signal.lower() == 'long5' or type_signal.lower() == 'throws':
        figi = None
    else:
        try:
            lock_state.acquire()
            support_tools = await state.get_data()
            lock_state.release()
            for short_ticker, param_family in support_tools['supp_tools'].items():
                if short_ticker == ticker.lower()[0:2]:
                    if len(ticker) == 2:
                        ticker = param_family['current_ticker']
                    for element in param_family['all_list']:
                        if ticker.lower() == element.lower():
                            ticker = element
                            break
                    else:
                        await message.answer(f"❌ ERROR: add_signal(): тикер {ticker} не поддерживается!")
                        return
                    break
        except KeyError as e:
            await message.answer(f"❌ ERROR: add_signal(): get 'supp_tools' except KeyError {e}")
            return

        status, ticker_param, err_mess = await tinv.get_param_instrument(ticker)
        if status:
            await message.answer(f"❌ ERROR: записи сигнала в файл: {err_mess}")
            return

        try:
            ticker = ticker_param['ticker']
            figi = ticker_param['figi']

            precision, err_val = await get_precision_from_value(ticker_param['precision'])
            if precision == -1:
                await message.answer(f"❌ ERROR: записи сигнала в файл: get_precision_from_value(): {err_val}")
                return

            if precision == 0:
                if '.' in value:
                    if int(value.split('.')[1]) > 0:
                        await message.answer(f"❌ ERROR: значение {value} не должно содержать дробной части")
                        return
                    else:
                        value = value.split('.')[0]
            else:
                try:
                    if len(value.split('.')[1]) > precision:
                        await message.answer(f"❌ ERROR: значение дробной части {value} не должно содержать "
                                             f"количество знаков > {precision}")
                        return
                except IndexError:
                    pass
        except KeyError as e:
            await message.answer(f"❌ ERROR: записи сигнала в файл: KeyError: {e}")
            return

    ret_val, err_mess = await journal.set_signal_to_file(ticker, type_signal.lower(), value, figi)
    if not ret_val:
        data = await journal.get_signals_from_file()
        lock_state.acquire()
        await state.update_data(signals=data)
        lock_state.release()
        if type_signal.lower() == 'long5' or type_signal.lower() == 'throws':
            await message.answer(f"📝 ✅ {type_signal.lower()} {ticker}")
        else:
            await message.answer(f"📝 ✅ set {ticker_param['ticker']} {type_signal.lower()} {value}")
    else:
        await message.answer(f"❌ ERROR: записи сигнала в файл: {err_mess}")


async def form_add_signal(event, state):
    text = (event.message.body.text or "").strip()

    lock_state.acquire()
    await state.update_data(value=text)
    data = await state.get_data()
    lock_state.release()

    # Удалить сообщение с введённым значением нельзя из-за ограничения MAX - бот может удалять только свои исходящие сообщения
    # Удаляем старое сообщение с клавиатурой
    try:
        await event.bot.delete_message(message_id=data["msg_id_for_del"])
    except KeyError:
        pass  # если не сохранили id — просто ничего не удаляем

    await add_signal(event.message, state, data['ticker'], data['type_signal'], data['value'])

    await state_clear_soft(state)


@router.message_callback(F.callback.payload == "cmd_del_signal")
async def callback_del_signal(event: MessageCallback):
    state = FSMContextLike(storage, event.from_user.user_id)

    # Кнопка "Отмена"
    buttons = [[
        {
            "type": "callback",
            "text": "Отмена",
            "payload": "cancel_signal",
        }
    ]]
    keyboard_attachment = Attachment(
        type="inline_keyboard",
        payload={"buttons": buttons},
    )

    msg = await event.message.answer(
        "Введите ID сигнала для удаления:",
        attachments=[keyboard_attachment],
    )

    lock_state.acquire()
    await state.update_data(msg_id_for_del=msg.message.body.mid)
    await state.set_state("Form.del_id")
    lock_state.release()


async def del_signal(message, state, id_signal):
    ret_val, err_mess = await journal.del_signal_from_file(id_signal)
    if ret_val:
        await message.answer(f"❌ ERROR: удаления сигнала: {err_mess}")
    else:
        data = await journal.get_signals_from_file()
        lock_state.acquire()
        await state.update_data(signals=data)
        lock_state.release()
        await message.answer(f"❎ OK: сигнал id={id_signal} успешно удалён.")


async def form_del_id(event, state):
    lock_state.acquire()
    data = await state.get_data()
    lock_state.release()

    # Удалить сообщение с введённым значением нельзя из-за ограничения MAX - бот может удалять только свои исходящие сообщения
    # Удаляем старое сообщение с клавиатурой
    try:
        await event.bot.delete_message(message_id=data["msg_id_for_del"])
    except KeyError:
        pass  # если не сохранили id — просто ничего не удаляем

    await del_signal(event.message, state, event.message.body.text)
    await state_clear_soft(state)


@router.message_created(Command("del"))
async def del_console(event: MessageCreated):
    state = FSMContextLike(storage, event.from_user.user_id)

    full_text = (event.message.body.text or "").strip()
    parts = full_text.split(maxsplit=1)
    command_args = parts[1] if len(parts) > 1 else ""
    if not command_args or len(command_args.split()) != 1:
        await event.message.answer(f"❌ Использование: /del id_signal")
        return

    id_signal: str = command_args
    try:
        int(id_signal)
    except (ValueError, TypeError):
        await event.message.answer(f"❌ ERROR: значение id_signal должно быть int.")
        return

    await del_signal(event.message, state, id_signal)


@router.message_created(Command("debug"))
async def debug_console(event: MessageCreated):
    state = FSMContextLike(storage, event.from_user.user_id)

    full_text = (event.message.body.text or "").strip()
    parts = full_text.split(maxsplit=1)
    command_args = parts[1] if len(parts) > 1 else ""
    if not command_args or len(command_args.split()) != 1:
        await event.message.answer(f"❌ Использование: /debug PARAM")
        return

    if command_args == "get_tasks":
        lock_state.acquire()
        await state.update_data(debug="get_tasks")
        lock_state.release()
    else:
        await event.message.answer(f"❌ ERROR: значение {command_args} не корректно.")
        return


@router.message_created(Command("long5"))
async def long5_console(event: MessageCreated):
    state = FSMContextLike(storage, event.from_user.user_id)

    full_text = (event.message.body.text or "").strip()
    parts = full_text.split(maxsplit=1)
    command_args = parts[1] if len(parts) > 1 else ""
    if not command_args or len(command_args.split()) != 1:
        await event.message.answer(f"❌ Использование: /long5 forts/moex")
        return

    if command_args not in ['forts', 'moex']:
        await event.message.answer(f"❌ Использование: /long5 forts/moex")
        return

    lock_state.acquire()
    all_data = await state.get_data()
    lock_state.release()
    try:
        for key, value in all_data['signals'].items():
            if value['type_signal'].lower() == 'long5' and value['market'] == command_args:
                await event.message.answer(f"📝 ✅ {value['type_signal'].lower()} {value['market']} уже установлен!")
                return
    except KeyError:
        await event.message.answer(f"❌ ERROR: long5_console(): format state")
        return

    await add_signal(event.message, state, command_args, "long5", None)


@router.message_created(F.message.body.text)
async def all_message(event: MessageCreated):
    state = FSMContextLike(storage, event.from_user.user_id)
    lock_state.acquire()
    curr_state = await state.get_state()
    lock_state.release()
    if curr_state == "Form.value":
        await form_add_signal(event, state)
    elif curr_state == "Form.del_id":
        await form_del_id(event, state)
    else:
        await event.message.answer(f"Добавить парсинг сообщение: {event.message.body.text} -- консоль")
