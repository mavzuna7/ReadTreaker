# handlers/delete_book.py
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async

router = Router()

class DeleteBook(StatesGroup):
    waiting_for_number = State()

@sync_to_async
def get_user_books_with_ids(telegram_id):
    from books.models import TelegramUser, UserBook
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        books = list(
            UserBook.objects.filter(user=user)
            .select_related('book')
            .order_by('id')
        )
        return books
    except TelegramUser.DoesNotExist:
        return []

@sync_to_async
def delete_user_book(book_id, telegram_id):
    from books.models import UserBook, TelegramUser
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        UserBook.objects.filter(id=book_id, user=user).delete()
        return True
    except:
        return False

@router.message(Command("delete_book"))
async def cmd_delete_book(message: Message, state: FSMContext):
    books = await get_user_books_with_ids(message.from_user.id)

    if not books:
        await message.answer(
            "📭 Похоже, у вас пока нет книг для удаления.\n"
            "Добавьте первую командой /add_book!"
        )
        return

    text = "🗑️ <b>Выберите книгу для удаления:</b>\n\n"
    for i, ub in enumerate(books, 1):
        status_icon = "✅" if ub.status == "read" else "⏳"
        text += f"{i}. {status_icon} <b>{ub.book.title}</b> — {ub.book.author}\n"
    
    text += "\n💬 Отправьте номер книги или напишите /cancel, чтобы отменить."
    await message.answer(text, parse_mode="HTML")
    await state.set_state(DeleteBook.waiting_for_number)
    await state.update_data(books=[b.id for b in books])

@router.message(DeleteBook.waiting_for_number)
async def process_delete_number(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "⏹️ Удаление отменено.\n\n"
            "Все ваши книги в безопасности! 📚",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    data = await state.get_data()
    book_ids = data.get("books", [])
    
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите <b>номер</b> из списка.", parse_mode="HTML")
        return

    num = int(message.text)
    if num < 1 or num > len(book_ids):
        await message.answer(
            f"Введите число от <b>1 до {len(book_ids)}</b>.",
            parse_mode="HTML"
        )
        return

    book_id = book_ids[num - 1]
    success = await delete_user_book(book_id, message.from_user.id)
    
    if success:
        await message.answer(
            "✅ Книга успешно удалена из вашей библиотеки!\n\n"
            "Хотите добавить новую? Попробуйте /add_book 📖"
        )
    else:
        await message.answer(
            "❌ Ой! Что-то пошло не так при удалении.\n"
            "Попробуйте снова или обратитесь к разработчику."
        )
    
    await state.clear()