import journal
from aiogram import Router, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Все роутеры нужно именовать так, чтобы не было конфликтов
router = Router()

class Form(StatesGroup):
    value = State()

@router.message(F.text.lower().contains('readme'))
async def cmd_help(message: types.Message):
    help_message = (
        "<b>Привет! Я бот.</b>\n\n"
        "<i>Вот некоторые доступные команды:</i>\n"
        "- /start: Начать взаимодействие с ботом\n"
        "- /help: Получить справку о командах бота"
    )
    await message.answer(help_message, parse_mode="HTML")

@router.message(F.text.lower().contains('просмотр сигналов'))
async def get_list_signal(message: types.Message):
    # TODO: возможно нужно брать текущие сигналы из опращиваемой структуры
    data = await journal.signals_from_file()
    if data is not None:
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

    builder.button(text="Volume", callback_data="typesignal_volume")
    builder.button(text="Price", callback_data="typesignal_price")

    await message.answer(
        "Выберите тип сигнала:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("typesignal_"))
async def handle_set_type_signal(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    type_signal = callback.data.split("_")[1]
    await state.update_data(type_signal=type_signal)

    builder.button(text="Si", callback_data=f"ticker_si_{type_signal}")
    builder.button(text="CNY", callback_data=f"ticker_cny_{type_signal}")

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

@router.message(F.text, Form.value)
async def form_state(message: types.Message, state: FSMContext):
    await state.update_data(value=message.text)
    data = await state.get_data()

    # TODO: проверить введенное число на кол-во знаков после запятой https://habr.com/ru/articles/822061/

    await message.delete()
    await message.bot.delete_message(chat_id=message.from_user.id, message_id=data['msg_id_for_del'])

    await message.answer(f"📝 ✅ <b>set {data['ticker']} {data['type_signal']} {data['value']}</b>")
    await state.clear()

# Хэндлер на остальные текстовые сообщения
@router.message()
async def unknown_message(message: types.Message):
    await message.answer(f"Добавить парсинг сообщение: {message.text} -- консоль")
