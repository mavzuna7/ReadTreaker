# handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    first_name = user.first_name or "друг"
    
    await message.answer(
        f"Привет, {first_name}! 👋\n\n"
        "✨ Я — <b>ReadTrackerBot</b>, ваш личный книжный трекер!\n\n"
        "📚 С моей помощью вы можете:\n"
        "• Добавлять книги в библиотеку\n"
        "• Просматривать свою коллекцию\n"
        "• Искать по названию, автору или жанру\n"
        "• Экспортировать всё в файл\n"
        "• Редактировать и удалять книги\n\n"
        "📖 Готовы начать? Просто выберите команду из меню!\n"
        "Удачного чтения! 📚💫",
        parse_mode="HTML"
    )