# handlers/favorites.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async

router = Router()

class ViewFavorites(StatesGroup):
    waiting_for_number = State()

@sync_to_async
def get_favorite_books(telegram_id):
    from books.models import TelegramUser, UserBook
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        favorites = list(
            UserBook.objects.filter(user=user, is_favorite=True)
            .select_related('book')
            .order_by('-date_read', 'id')
        )
        return favorites
    except:
        return []

@sync_to_async
def get_favorite_book_by_index(telegram_id, index):
    from books.models import TelegramUser, UserBook
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        all_favs = list(
            UserBook.objects.filter(user=user, is_favorite=True)
            .select_related('book')
            .order_by('-date_read', 'id')
        )
        if 0 <= index < len(all_favs):
            return all_favs[index]
        return None
    except:
        return None

@router.message(Command("favorites"))
async def cmd_favorites(message: Message, state: FSMContext):
    favorites = await get_favorite_books(message.from_user.id)

    if not favorites:
        await message.answer("🤍 У вас нет книг в избранном.")
        return

    text = "⭐ Ваши избранные книги:\n\n"
    for i, ub in enumerate(favorites, 1):
        fav_icon = "❤️" if ub.is_favorite else "🤍"
        status = "✅" if ub.status == "read" else "⏳"
        rating = f" ⭐{ub.rating}" if ub.rating else ""
        date = f" ({ub.date_read})" if ub.date_read else ""
        text += f"{i}. {fav_icon} {status} {ub.book.title} — {ub.book.author}{rating}{date}\n"

    text += "\n📖 Отправьте номер для просмотра подробностей или /cancel для отмены."
    await message.answer(text)
    await state.set_state(ViewFavorites.waiting_for_number)
    await state.update_data(book_ids=[b.id for b in favorites])

@router.message(ViewFavorites.waiting_for_number)
async def process_favorite_number(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Просмотр отменён.")
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

    book_index = num - 1
    ub = await get_favorite_book_by_index(message.from_user.id, book_index)
    
    if not ub:
        await message.answer("❌ Книга не найдена.")
        await state.clear()
        return

    # Формируем подробную карточку (как в my_books)
    text = f"⭐ <b>{ub.book.title}</b>\n"
    text += f"✍️ Автор: {ub.book.author}\n"
    if ub.book.genre:
        text += f"📚 Жанр: {ub.book.genre}\n"
    if ub.book.year:
        text += f"📅 Год: {ub.book.year}\n"
    text += f"📌 Статус: {'Прочитано' if ub.status == 'read' else 'Хочу прочитать'}\n"
    
    if ub.status == "read":
        if ub.rating:
            text += f"⭐ Оценка: {ub.rating}\n"
        if ub.date_read:
            text += f"📆 Дата прочтения: {ub.date_read}\n"
    
    if ub.description:
        text += f"\n📖 <b>Описание:</b>\n{ub.description}\n"
    if ub.review:
        text += f"\n💭 <b>Мои впечатления:</b>\n{ub.review}\n"

    # Отправляем обложку
    cover_path = None
    if ub.book.cover_path:
        from pathlib import Path
        BASE_DIR = Path(__file__).resolve().parent.parent
        possible_paths = [
            BASE_DIR / ub.book.cover_path,
            BASE_DIR / "media" / "covers" / ub.book.cover_path.split("/")[-1]
        ]
        for p in possible_paths:
            if p.exists():
                cover_path = str(p)
                break

    caption = text[:1024]
    if cover_path:
        try:
            with open(cover_path, 'rb') as photo:
                await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
            await state.clear()
            return
        except:
            pass

    await message.answer(text, parse_mode="HTML")
    await state.clear()