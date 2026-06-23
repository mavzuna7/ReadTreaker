# handlers/my_books.py
import os
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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
def get_book_by_id(userbook_id):
    from books.models import UserBook

    try:
        return UserBook.objects.select_related('book').get(id=userbook_id)
    except UserBook.DoesNotExist:
        return None

def books_keyboard(all_books):
    buttons = []

    for ub in all_books:
        buttons.append([
            InlineKeyboardButton(
                text=f"📘 {ub.book.title}",
                callback_data=f"book_{ub.id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("my_books"))
async def cmd_my_books(message: Message, state: FSMContext):
    read_books, want_books = await get_user_books_with_ids(message.from_user.id)

    if not read_books and not want_books:
        await message.answer(
            "📭 Похоже, у вас пока нет книг.\n"
            "Добавьте первую командой /add_book!"
        )
        return
    
    all_books = read_books + want_books

    await message.answer(
        "📚 <b>Ваша библиотека</b>\n\nВыберите книгу:",
        parse_mode="HTML",
        reply_markup=books_keyboard(all_books)
    )

    

@router.callback_query(F.data.startswith("book_"))
async def show_book(callback: CallbackQuery):
    userbook_id = int(callback.data.split("_")[1])

    ub = await get_book_by_id(userbook_id)

    if not ub:
        await callback.answer("Книга не найдена")
        return

    text = f"📘 <b>{ub.book.title}</b>\n"
    text += f"✍️ Автор: {ub.book.author}\n"

    if ub.book.genre:
        text += f"📚 Жанр: {ub.book.genre}\n"

    if ub.book.year:
        text += f"📅 Год: {ub.book.year}\n"

    text += f"📌 Статус: {'Прочитано' if ub.status == 'read' else 'Хочу прочитать'}\n"

    if ub.rating:
        text += f"⭐ Оценка: {ub.rating}\n"

    if ub.date_start and ub.date_end:
        text += (
            f"\n📅 Период чтения:\n"
            f"• Начато: {ub.date_start}\n"
            f"• Завершено: {ub.date_end}\n"
        )

    if ub.description:
        text += f"\n📖 <b>Описание:</b>\n{ub.description}\n"

    if ub.review:
        text += f"\n💭 <b>Мои впечатления:</b>\n{ub.review}\n"

    cover_path = ub.book.cover_path
    found_path = None

    print("=" * 50)
    print("cover_path из БД:", ub.book.cover_path)
    print("=" * 50)

    if cover_path:
        full_path = BASE_DIR / cover_path

        if cover_path:
            candidates = [
                BASE_DIR / cover_path,
                BASE_DIR / "media" / "covers" / Path(cover_path).name,
                BASE_DIR / "media" / cover_path,
            ]

        for cand in candidates:
            print("Проверяем:", cand)
            print("Существует:", cand.exists())

            if cand.exists():
                found_path = str(cand)
                print("НАЙДЕН ФАЙЛ:", found_path)
                break

        if full_path.exists():
            photo = FSInputFile(str(full_path))

            await callback.message.answer_photo(
                photo=photo,
                caption=text[:1024],
                parse_mode="HTML"
            )

            await callback.answer()
            return

    await callback.message.answer(
        text,
        parse_mode="HTML"
    )