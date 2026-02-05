# handlers/delete_book.py
from aiogram import Router
from aiogram.types import Message
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
    print(f"📚 Найдено книг: {len(books)}")  # ← отладка

    if not books:
        await message.answer("📭 У вас нет книг для удаления.")
        return

    # Формируем список
    text = "🗑️ Выберите книгу для удаления:\n\n"
    for i, ub in enumerate(books, 1):
        status = "✅" if ub.status == "read" else "⏳"
        text += f"{i}. {status} {ub.book.title} — {ub.book.author}\n"
    
    text += "\nВведите номер книги или /cancel для отмены."
    await message.answer(text)
    await state.set_state(DeleteBook.waiting_for_number)
    # Сохраняем список книг в состоянии
    await state.update_data(books=[b.id for b in books])

@router.message(DeleteBook.waiting_for_number)
async def process_delete_number(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Удаление отменено.")
        return

    data = await state.get_data()
    book_ids = data.get("books", [])
    
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите номер из списка.")
        return

    num = int(message.text)
    if num < 1 or num > len(book_ids):
        await message.answer(f"Введите число от 1 до {len(book_ids)}.")
        return

    book_id = book_ids[num - 1]
    success = await delete_user_book(book_id, message.from_user.id)
    
    if success:
        await message.answer("✅ Книга удалена!")
    else:
        await message.answer("❌ Не удалось удалить книгу.")
    
    await state.clear()