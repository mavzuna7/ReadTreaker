# handlers/favorite.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async

router = Router()

class FavoriteState(StatesGroup):
    selecting_book = State()

@sync_to_async
def get_user_books_for_favorites(telegram_id):
    from books.models import TelegramUser, UserBook
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        books = list(
            UserBook.objects.filter(user=user)
            .select_related('book')
            .order_by('-date_read', 'id')
        )
        return books
    except:
        return []

@sync_to_async
def toggle_favorite(book_id, telegram_id):
    from books.models import UserBook, TelegramUser
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        ub = UserBook.objects.get(id=book_id, user=user)
        ub.is_favorite = not ub.is_favorite
        ub.save()
        return ub.is_favorite, ub.book.title
    except:
        return None, None

@router.message(Command("favorite"))
async def cmd_favorite(message: Message, state: FSMContext):
    books = await get_user_books_for_favorites(message.from_user.id)

    if not books:
        await message.answer("📭 У вас нет книг для добавления в избранное.")
        return

    text = "⭐ Выберите книгу, чтобы добавить/удалить из избранного:\n\n"
    for i, ub in enumerate(books, 1):
        fav_icon = "❤️" if ub.is_favorite else "🤍"
        status = "✅" if ub.status == "read" else "⏳"
        text += f"{i}. {fav_icon} {status} {ub.book.title} — {ub.book.author}\n"

    text += "\nОтправьте номер книги или /cancel для отмены."
    await message.answer(text)
    await state.set_state(FavoriteState.selecting_book)
    await state.update_data(book_ids=[b.id for b in books])

@router.message(FavoriteState.selecting_book)
async def process_favorite_selection(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Действие отменено.")
        return

    data = await state.get_data()
    book_ids = data.get("book_ids", [])
    
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите номер из списка.")
        return

    num = int(message.text)
    if num < 1 or num > len(book_ids):
        await message.answer(f"Введите число от 1 до {len(book_ids)}.")
        return

    book_id = book_ids[num - 1]
    is_now_favorite, title = await toggle_favorite(book_id, message.from_user.id)

    if is_now_favorite is None:
        await message.answer("❌ Ошибка при обновлении избранного.")
    else:
        action = "добавлена в избранное" if is_now_favorite else "удалена из избранного"
        await message.answer(f"✅ Книга «{title}» {action}!")

    await state.clear()