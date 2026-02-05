# handlers/add_book.py
import os
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async

BASE_DIR = Path(__file__).resolve().parent.parent
router = Router()

class AddBook(StatesGroup):
    title = State()
    author = State()
    genre = State()
    year = State()
    status = State()
    cover = State()
    description = State()
    review = State()
    rating = State()
    date_read = State()

@router.message(Command("add_book"))
async def cmd_add_book(message: Message, state: FSMContext):
    await message.answer(
        "📘 Введите название книги.\n"
        "Отменить: /cancel"
    )
    await state.set_state(AddBook.title)

@router.message(AddBook.title)
async def process_title(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(title=message.text.strip())
    await message.answer("✍️ Введите автора.\nОтменить: /cancel")
    await state.set_state(AddBook.author)

@router.message(AddBook.author)
async def process_author(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(author=message.text.strip())
    await message.answer("📚 Введите жанр.\nОтменить: /cancel")
    await state.set_state(AddBook.genre)

@router.message(AddBook.genre)
async def process_genre(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(genre=message.text.strip())
    await message.answer("📅 Введите год издания (или пропустите).\nОтменить: /cancel")
    await state.set_state(AddBook.year)

@router.message(AddBook.year)
async def process_year(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    year = None
    if message.text.isdigit():
        year = int(message.text)
    await state.update_data(year=year)
    await message.answer("✅ Книга уже прочитана? Ответьте: да / нет\nОтменить: /cancel")
    await state.set_state(AddBook.status)

@router.message(AddBook.status)
async def process_status(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    text = message.text.lower().strip()
    if text in ["да", "yes", "y"]:
        await state.update_data(status="read")
    elif text in ["нет", "no", "n"]:
        await state.update_data(status="want_to_read")
    else:
        await message.answer("Пожалуйста, ответьте: да или нет\nОтменить: /cancel")
        return

    await message.answer("🖼️ Отправьте обложку книги (фото) или напишите «пропустить»:\nОтменить: /cancel")
    await state.set_state(AddBook.cover)

@router.message(AddBook.cover)
async def process_cover(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return

    cover_path = ""
    
    if message.photo:
        photo = message.photo[-1]
        file_info = await message.bot.get_file(photo.file_id)
        
        covers_dir = BASE_DIR / "media" / "covers"
        covers_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{photo.file_unique_id}.jpg"
        full_path = covers_dir / filename
        await message.bot.download_file(file_info.file_path, full_path)
        
        # Сохраняем ОТНОСИТЕЛЬНЫЙ путь от корня проекта
        cover_path = str(full_path.relative_to(BASE_DIR))
        await message.answer("✅ Обложка сохранена!")
    elif message.text and message.text.strip().lower() == "пропустить":
        await message.answer("⏭️ Обложка пропущена.")
    else:
        await message.answer("Пожалуйста, отправьте фото или напишите «пропустить».")
        return

    await state.update_data(cover_path=cover_path)
    await message.answer("📖 Введите описание книги или пропустите:\nОтменить: /cancel")
    await state.set_state(AddBook.description)

@router.message(AddBook.description)
async def process_description(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(description=message.text.strip())
    data = await state.get_data()
    if data["status"] == "read":
        await message.answer("💭 Ваши впечатления от книги (рецензия) или пропустите:\nОтменить: /cancel")
        await state.set_state(AddBook.review)
    else:
        await save_book_to_db(message, state)

@router.message(AddBook.review)
async def process_review(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(review=message.text.strip())
    await message.answer("⭐ Оцените книгу от 1 до 5:\nОтменить: /cancel")
    await state.set_state(AddBook.rating)

@router.message(AddBook.rating)
async def process_rating(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    if message.text.isdigit() and 1 <= int(message.text) <= 5:
        await state.update_data(rating=int(message.text))
        await message.answer("📆 Введите дату прочтения (ГГГГ-ММ-ДД) или напишите 'сегодня':\nОтменить: /cancel")
        await state.set_state(AddBook.date_read)
    else:
        await message.answer("Пожалуйста, введите число от 1 до 5.\nОтменить: /cancel")

@router.message(AddBook.date_read)
async def process_date_read(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    date_str = message.text.strip().lower()
    if date_str == "сегодня":
        from datetime import date
        date_read = date.today()
    else:
        try:
            from datetime import datetime
            date_read = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            await message.answer("Неверный формат. Используйте ГГГГ-ММ-ДД или 'сегодня'.\nОтменить: /cancel")
            return
    await state.update_data(date_read=date_read)
    await save_book_to_db(message, state)

@sync_to_async
def _save_to_db(user_id, username, data):
    try:
        from books.models import TelegramUser, Book, UserBook
        user, created = TelegramUser.objects.get_or_create(
            telegram_id=user_id,
            defaults={"username": username}
        )
        book, created = Book.objects.get_or_create(
            title=data["title"],
            defaults={
                "author": data.get("author", ""),
                "genre": data.get("genre", ""),
                "year": data.get("year"),
                "cover_path": data.get("cover_path", "")
            }
        )
        UserBook.objects.create(
            user=user,
            book=book,
            status=data["status"],
            rating=data.get("rating"),
            date_read=data.get("date_read"),
            description=data.get("description", ""),
            review=data.get("review", "")
        )
        print("✅ Книга сохранена в БД!")
    except Exception as e:
        print("❌ Ошибка сохранения:", e)

async def save_book_to_db(message: Message, state: FSMContext):
    data = await state.get_data()
    await _save_to_db(
        user_id=message.from_user.id,
        username=message.from_user.username,
        data=data
    )
    await message.answer("✅ Книга успешно добавлена!")
    await state.clear()

async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Добавление книги отменено.")