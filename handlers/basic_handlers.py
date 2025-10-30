from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

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
    # Создаем объект билдера для Reply-клавиатуры
    builder = ReplyKeyboardBuilder()
    
    # Добавляем кнопки
    builder.button(text="Start")
    builder.button(text="/help")
    
    # Указываем, сколько кнопок будет в одном ряду (в данном случае 2)
    builder.adjust(2)
    
    await message.answer(
        "Привет! Я эхо-бот. Отправь мне любое сообщение, и я его повторю.",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

# Хэндлер на остальные текстовые сообщения
@router.message()
async def echo_message(message: types.Message):
    await message.answer(f"Я получил твое сообщение: {message.text}")
