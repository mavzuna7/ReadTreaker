# handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    await message.answer(
        f"Привет, {user.first_name}! 👋\n"
        "Я — ReadTreakerBot, твой помощник в учёте прочитанных книг.\n\n"
        "Скоро появится возможность добавлять книги!"
    )