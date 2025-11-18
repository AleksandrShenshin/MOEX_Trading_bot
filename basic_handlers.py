import journal
from aiogram import Router, types, F
from aiogram.filters import CommandObject
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from general import get_support_instruments, get_support_signals

# Все роутеры нужно именовать так, чтобы не было конфликтов
router = Router()


class Form(StatesGroup):
    value = State()


@router.message(Command("help"))
@router.message(F.text.lower().contains('readme'))
async def cmd_help(message: types.Message):
    readme_message = "<b>Поддерживаемые команды:</b>\n"
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
        await message.answer(readme_message)


@router.message(Command("get_list_ticker"))
async def get_support_ticker(message: types.Message):
    support_ticker = ""
    supp_instr = await get_support_instruments()
    for text_ticker, param_ticker in supp_instr.items():
        if not support_ticker:
            support_ticker += text_ticker.lower()
        else:
            support_ticker += f", {text_ticker.lower()}"
    await message.answer(support_ticker)


@router.message(Command("get_signals"))
@router.message(F.text.lower().contains('просмотр сигналов'))
async def get_list_signal(message: types.Message):
    # TODO: возможно нужно брать текущие сигналы из опращиваемой структуры
    data = await journal.signals_from_file()
    if len(data) != 0:
        list_signals = f"Активные сигналы:\n"
        try:
            for key, value in data.items():
                list_signals += f"{key}: {value['ticker']} {value['type_signal']} {value['value']}\n"
            await message.answer(list_signals)
        except KeyError:
            await message.answer("❌ <b>ОШИБКА:</b> получения данных")
    else:
        await message.answer(f"Нет активных сигналов")


@router.message(F.text.lower().contains('добавить сигнал'))
async def cmd_actions(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()

    supp_signals = await get_support_signals()
    for text_signal, param_signal in supp_signals.items():
        builder.row(
            InlineKeyboardButton(
                text=text_signal,
                callback_data=f'typesignal_{text_signal.lower()}'
            )
        )
    builder.adjust(2)

    await message.answer(
        "Выберите тип сигнала:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("typesignal_"))
async def handle_set_type_signal(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    type_signal = callback.data.split("_")[1]
    await state.update_data(type_signal=type_signal)

    supp_instr = await get_support_instruments()
    for text_ticker, param_ticker in supp_instr.items():
        # TODO: заменить text_ticker на действующий фьючерс
        builder.row(
            InlineKeyboardButton(
                text=text_ticker,
                callback_data=f'ticker_{text_ticker}'
            )
        )
    builder.adjust(3)

    # Редактируем текст исходного сообщения
    await callback.message.edit_text(
        "Выберите инструмент:",
        reply_markup=builder.as_markup()
    )
    # Отвечаем на callback, чтобы убрать "часики" на кнопке
    await callback.answer()


@router.callback_query(F.data.startswith("ticker_"))
async def handle_set_ticker(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    ticker = callback.data.split("_")[1]
    await state.update_data(ticker=ticker)
    await state.update_data(msg_id_for_del=callback.message.message_id)
    data = await state.get_data()

    builder.button(text="Отмена", callback_data=f"cancel_signal")

    # Редактируем текст исходного сообщения
    await callback.message.edit_text(
        f"Введите значение <b>{data['ticker']}</b> <b>{data['type_signal']:}</b>",
        reply_markup=builder.as_markup()
    )
    await state.set_state(Form.value)


@router.callback_query(F.data == "cancel_signal")
async def handle_cancel_signal(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.clear()


async def add_signal(message, ticker, type_signal, value):
    supp_instr = await get_support_instruments()
    for text_ticker, param_ticker in supp_instr.items():
        if text_ticker.lower() == ticker.lower():
            try:
                precision = int(param_ticker['precision'])
                break
            except (KeyError, NameError) as e:
                await message.answer(f"❌ <b>ERROR:</b> add_signal(): get 'precision' except {e}")
                return
    else:
        await message.answer(f"❌ <b>ERROR:</b> тикер {ticker} не поддерживается")
        return

    supp_signals = await get_support_signals()
    for text_signal, param_signal in supp_signals.items():
        if text_signal.lower() == type_signal.lower():
            break
    else:
        await message.answer(f"❌ <b>ERROR:</b> тип сигнала {type_signal} не корректный")
        return

    if type_signal.lower() == 'volume':
        try:
            int(value)
        except ValueError:
            await message.answer(f"❌ <b>ERROR:</b> значение {value} должно быть целым для {type_signal}")
            return
    elif type_signal.lower() == 'price':
        value = value.replace(',', '.')
        try:
            float(value)
        except ValueError:
            await message.answer(f"❌ <b>ERROR:</b> значение {value} должно содержать только цифры")
            return

        if precision == 0:
            if '.' in value:
                if int(value.split('.')[1]) > 0:
                    await message.answer(f"❌ <b>ERROR:</b> значение {value} не должно содержать дробной части")
                    return
        else:
            try:
                if len(value.split('.')[1]) > precision:
                    await message.answer(f"❌ <b>ERROR:</b> значение дробной части {value} не должно содержать "
                                         f"количество знаков > {precision}")
                    return
            except IndexError:
                pass

    # TODO: печатать полный тикер
    ret_val, err_mess = await journal.signals_to_file(ticker.lower(), type_signal.lower(), value)
    if not ret_val:
        await message.answer(f"📝 ✅ <b>set {ticker.lower()} {type_signal.lower()} {value}</b>")
    else:
        await message.answer(f"❌ <b>ERROR:</b> записи сигнала в файл: {err_mess}")


@router.message(F.text, Form.value)
async def form_state(message: types.Message, state: FSMContext):
    await state.update_data(value=message.text)
    data = await state.get_data()

    await message.delete()
    await message.bot.delete_message(chat_id=message.from_user.id, message_id=data['msg_id_for_del'])

    await add_signal(message, data['ticker'], data['type_signal'], data['value'])
    await state.clear()


@router.message(Command("set"))
async def set_console(message: types.Message, command: CommandObject):
    command_args: str = command.args
    ticker, param_signal, value = command_args.split()

    supp_signals = await get_support_signals()
    for text_signal, param_val in supp_signals.items():
        try:
            if param_signal != param_val['param']:
                continue
        except KeyError as e:
            await message.answer(f"❌ <b>ERROR:</b> set_console(): KeyError {e}")
            break
        else:
            await add_signal(message, ticker, text_signal, value)
            break
    else:
        await message.answer(f"❌ <b>ERROR:</b> параметр {param_signal} не корректный.")


# Хэндлер на остальные текстовые сообщения
@router.message()
async def unknown_message(message: types.Message):
    await message.answer(f"Добавить парсинг сообщение: {message.text} -- консоль")
