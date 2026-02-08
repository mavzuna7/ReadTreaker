# handlers/cancel.py
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "🤔 Похоже, вы ни во что не погружены!\n"
            "Можно начать с команды /add_book или /search."
        )
        return

    await state.clear()
    await message.answer(
        "⏹️ Действие отменено.\n\n"
        "Не переживайте — все ваши книги в безопасности! 📚\n"
        "Готовы продолжить? Просто выберите новую команду!",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )