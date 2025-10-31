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

@router.message(Command("actions"))
async def cmd_actions(message: types.Message):
    builder = InlineKeyboardBuilder()

    builder.button(text="Показать уведомление", callback_data="show_alert")
    builder.button(text="Сменить это сообщение", callback_data="edit_message")

    await message.answer(
        "Нажми на кнопку, чтобы выполнить действие:",
        reply_markup=builder.as_markup()
    )

# Хэндлер на остальные текстовые сообщения
@router.message()
async def echo_message(message: types.Message):
    await message.answer(f"Я получил твое сообщение: {message.text}")

# Хэндлер для обработки нажатия на кнопку "Показать уведомление"
@router.callback_query(F.data == "show_alert")
async def handle_show_alert(callback: types.CallbackQuery):
    await callback.answer(
        "Это всплывающее уведомление!",
        show_alert=True # Делает уведомление модальным окном
    )

# Хэндлер для обработки нажатия на кнопку "Сменить это сообщение"
@router.callback_query(F.data == "edit_message")
async def handle_edit_message(callback: types.CallbackQuery):
    # Редактируем текст исходного сообщения
    await callback.message.edit_text("Сообщение было изменено!")
    # Отвечаем на callback, чтобы убрать "часики" на кнопке
    await callback.answer()
