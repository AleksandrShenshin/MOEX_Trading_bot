from aiogram import Router, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Все роутеры нужно именовать так, чтобы не было конфликтов
router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_message = (
        "<b>Привет! Я бот.</b>\n\n"
        "<i>Вот некоторые доступные команды:</i>\n"
        "- /start: Начать взаимодействие с ботом\n"
        "- /help: Получить справку о командах бота"
    )
    await message.answer(help_message, parse_mode="HTML")

@router.message(F.text == "Просмотр сигналов")
async def get_list_signal(message: types.Message):
    await message.answer(f"Активные сигналы: {message.text}")

@router.message(F.text == "Добавить сигнал")
async def cmd_actions(message: types.Message):
    builder = InlineKeyboardBuilder()

    builder.button(text="Volume", callback_data="typesignal_volume")
    builder.button(text="Price", callback_data="typesignal_price")

    await message.answer(
        "Выберите тип сигнала:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("typesignal_"))
async def handle_set_type_signal(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    type_signal = callback.data.split("_")[1]

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
async def handle_set_ticker(callback: types.CallbackQuery):
    # Редактируем текст исходного сообщения
    await callback.message.edit_text(
        f"Текущий инструмент и тип сигнала: {callback.data}"
    )

# Хэндлер на остальные текстовые сообщения
@router.message()
async def unknown_message(message: types.Message):
    await message.answer(f"Добавить парсинг сообщение: {message.text} -- консоль")
