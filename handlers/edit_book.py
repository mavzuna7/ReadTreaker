# handlers/edit_book.py
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
router = Router()

class EditBook(StatesGroup):
    selecting_book = State()
    selecting_field = State()
    entering_new_value = State()
    uploading_new_cover = State()

@sync_to_async
def get_user_books(telegram_id):
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
def update_book_field(book_id, field, value):
    from books.models import UserBook
    UserBook.objects.filter(id=book_id).update(**{field: value})

@sync_to_async
def update_book_cover(book_id, cover_rel_path):
    from books.models import UserBook, Book
    ub = UserBook.objects.select_related('book').get(id=book_id)
    Book.objects.filter(id=ub.book.id).update(cover_path=cover_rel_path)

@router.message(Command("edit_book"))
async def cmd_edit_book(message: Message, state: FSMContext):
    books = await get_user_books(message.from_user.id)
    if not books:
        await message.answer(
            "📭 Похоже, у вас пока нет книг для редактирования.\n"
            "Добавьте первую командой /add_book!"
        )
        return

    text = "✏️ <b>Выберите книгу для редактирования:</b>\n\n"
    for i, ub in enumerate(books, 1):
        status_icon = "✅" if ub.status == "read" else "⏳"
        text += f"{i}. {status_icon} <b>{ub.book.title}</b> — {ub.book.author}\n"
    
    text += "\n💬 Отправьте номер книги или напишите /cancel."
    await message.answer(text, parse_mode="HTML")
    await state.set_state(EditBook.selecting_book)
    await state.update_data(book_ids=[b.id for b in books])

@router.message(EditBook.selecting_book)
async def process_select_book(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "⏹️ Редактирование отменено.\n\n"
            "Все ваши данные остались без изменений! 📚",
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

    book_id = book_ids[num - 1]
    await state.update_data(editing_book_id=book_id)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Описание")],
            [KeyboardButton(text="Впечатления")],
            [KeyboardButton(text="Оценка")],
            [KeyboardButton(text="Дата прочтения")],
            [KeyboardButton(text="Обложка")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("✨ Что хотите изменить?", reply_markup=kb)
    await state.set_state(EditBook.selecting_field)

@router.message(EditBook.selecting_field)
async def process_select_field(message: Message, state: FSMContext):
    if message.text == "Отмена" or message.text == "/cancel":
        await state.clear()
        await message.answer(
            "⏹️ Редактирование отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    field_map = {
        "Описание": "description",
        "Впечатления": "review",
        "Оценка": "rating",
        "Дата прочтения": "date_read",
        "Обложка": "cover"
    }

    if message.text not in field_map:
        await message.answer("Пожалуйста, выберите поле из меню.")
        return

    field = field_map[message.text]
    await state.update_data(editing_field=field)

    if field == "cover":
        await message.answer(
            "🖼️ Отправьте <b>новую обложку</b> (фото) или напишите «пропустить».",
            parse_mode="HTML"
        )
        await state.set_state(EditBook.uploading_new_cover)
    else:
        label = message.text.lower()
        await message.answer(f"✍️ Введите новое значение для «{label}»:")
        await state.set_state(EditBook.entering_new_value)

@router.message(EditBook.entering_new_value)
async def process_new_value(message: Message, state: FSMContext):
    data = await state.get_data()
    book_id = data["editing_book_id"]
    field = data["editing_field"]

    if field == "rating":
        if not message.text.isdigit() or not (1 <= int(message.text) <= 5):
            await message.answer("Оценка должна быть от <b>1 до 5</b>.", parse_mode="HTML")
            return
        value = int(message.text)
    elif field == "date_read":
        date_str = message.text.strip()
        if date_str.lower() == "сегодня":
            from datetime import date
            value = date.today()
        else:
            try:
                from datetime import datetime
                value = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                await message.answer("Неверный формат. Используйте <b>ГГГГ-ММ-ДД</b> или «сегодня».", parse_mode="HTML")
                return
    else:
        value = message.text.strip()

    await update_book_field(book_id, field, value)
    await message.answer("✅ Изменения успешно сохранены!\n\nХотите отредактировать ещё что-то? Напишите /edit_book")
    await state.clear()

@router.message(EditBook.uploading_new_cover)
async def process_new_cover(message: Message, state: FSMContext):
    data = await state.get_data()
    book_id = data["editing_book_id"]

    if message.text and message.text.strip().lower() == "пропустить":
        await message.answer("⏭️ Обложка осталась без изменений.")
        await state.clear()
        return

    if not message.photo:
        await message.answer("Пожалуйста, отправьте <b>фото</b> или напишите «пропустить».", parse_mode="HTML")
        return

    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    covers_dir = BASE_DIR / "media" / "covers"
    covers_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{photo.file_unique_id}.jpg"
    full_path = covers_dir / filename
    await message.bot.download_file(file_info.file_path, full_path)
    cover_rel_path = str(full_path.relative_to(BASE_DIR))

    await update_book_cover(book_id, cover_rel_path)
    await message.answer("✅ Новая обложка успешно сохранена!")
    await state.clear()