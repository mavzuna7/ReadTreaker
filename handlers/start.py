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
        "✨ Я — <b>ReadTreakerBot</b>, ваш личный книжный трекер!\n\n"
        "📚 С моей помощью вы можете:\n"
        "• Добавлять книги в библиотеку (/add_book)\n"
        "• Просматривать свою коллекцию (/my_books)\n"
        "• Искать по названию, автору или жанру (/search)\n"
        "• Получать персональные рекомендации (/recommend)\n"
        "• Экспортировать всё в файл (/export)\n"
        "• Редактировать и удалять книги (/edit_book, /delete_book)\n\n"
        "📖 Готовы начать? Просто выберите команду из меню!\n"
        "Удачного чтения! 📚💫",
        parse_mode="HTML"
    )