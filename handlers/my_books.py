# handlers/my_books.py
import os
from pathlib import Path
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from aiogram.types import FSInputFile

BASE_DIR = Path(__file__).resolve().parent.parent
router = Router()

class ViewBooks(StatesGroup):
    waiting_for_number = State()

@sync_to_async
def get_user_books_with_ids(telegram_id):
    from books.models import TelegramUser, UserBook
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        read_books = list(
            UserBook.objects.filter(user=user, status='read')
            .select_related('book')
        )
        want_books = list(
            UserBook.objects.filter(user=user, status='want_to_read')
            .select_related('book')
        )
        return read_books, want_books
    except TelegramUser.DoesNotExist:
        return [], []

@sync_to_async
def get_book_by_index(telegram_id, index):
    from books.models import TelegramUser, UserBook
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        all_books = list(
            UserBook.objects.filter(user=user)
            .select_related('book')
            .order_by('-date_read', 'id')
        )
        if 0 <= index < len(all_books):
            return all_books[index]
        return None
    except:
        return None

@router.message(Command("my_books"))
async def cmd_my_books(message: Message, state: FSMContext):
    read_books, want_books = await get_user_books_with_ids(message.from_user.id)

    if not read_books and not want_books:
        await message.answer(
            "📭 Похоже, у вас пока нет книг.\n"
            "Добавьте первую командой /add_book!"
        )
        return

    text = "📚 <b>Ваши книги:</b>\n\n"
    all_books = []

    if read_books:
        text += "✅ <b>Прочитано:</b>\n"
        for ub in read_books:
            all_books.append(ub)
            rating = f" ⭐{ub.rating}" if ub.rating else ""
            date = f" ({ub.date_read})" if ub.date_read else ""
            text += f"{len(all_books)}. <b>{ub.book.title}</b> — {ub.book.author}{rating}{date}\n"

    if want_books:
        text += "\n⏳ <b>Хочу прочитать:</b>\n"
        for ub in want_books:
            all_books.append(ub)
            text += f"{len(all_books)}. <b>{ub.book.title}</b> — {ub.book.author}\n"

    text += "\n📖 Отправьте <b>номер книги</b>, чтобы посмотреть подробности.\n"
    text += "❌ Напишите /cancel, чтобы выйти."

    await message.answer(text, parse_mode="HTML")
    await state.set_state(ViewBooks.waiting_for_number)
    await state.update_data(book_ids=[b.id for b in all_books])

@router.message(ViewBooks.waiting_for_number)
async def process_book_number(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "⏹️ Просмотр отменён.\n\n"
            "Все ваши книги на месте! 📚",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    data = await state.get_data()
    book_ids = data.get("book_ids", [])
    
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

    book_index = num - 1
    ub = await get_book_by_index(message.from_user.id, book_index)
    
    if not ub:
        await message.answer("❌ Книга не найдена.")
        await state.clear()
        return

    # Формируем подробную карточку
    text = f"📘 <b>{ub.book.title}</b>\n"
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

    # === ОТПРАВКА ОБЛОЖКИ ===
    cover_path = ub.book.cover_path
    found_path = None

    if cover_path:
        candidates = [
            BASE_DIR / cover_path,
            BASE_DIR / "media" / "covers" / Path(cover_path).name,
            BASE_DIR / "media" / cover_path,
        ]
        for cand in candidates:
            if cand.exists():
                found_path = str(cand)
                break

    if found_path:
        try:
            photo = FSInputFile(found_path)
            await message.answer_photo(
                photo=photo,
                caption=text[:1024],
                parse_mode="HTML"
            )
            await state.clear()
            return
        except Exception as e:
            print(f"❌ Ошибка отправки обложки: {e}")

    # Если фото нет — просто текст
    await message.answer(text, parse_mode="HTML")
    await state.clear()