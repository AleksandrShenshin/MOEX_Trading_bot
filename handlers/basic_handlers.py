from aiogram import Router, types
from aiogram.filters.command import Command

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

# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я эхо-бот. Отправь мне любое сообщение, и я его повторю.")

# Хэндлер на остальные текстовые сообщения
@router.message()
async def echo_message(message: types.Message):
    await message.answer(f"Я получил твое сообщение: {message.text}")
