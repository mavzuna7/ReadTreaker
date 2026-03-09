# handlers/add_book.py
import os
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
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
    user = message.from_user.first_name or "друг"
    await message.answer(
        f"Привет, {user}! 📖\n\n"
        "Давайте добавим новую книгу в вашу библиотеку!\n\n"
        "Напишите <b>название книги</b> — например, «1984» или «Мастер и Маргарита».\n\n"
        "💡 В любой момент можно отменить — просто напишите /cancel",
        parse_mode="HTML"
    )
    await state.set_state(AddBook.title)

@router.message(AddBook.title)
async def process_title(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(title=message.text.strip())
    await message.answer(
        "Отличный выбор! 👏\n\n"
        "Теперь укажите <b>автора</b> этой книги.",
        parse_mode="HTML"
    )
    await state.set_state(AddBook.author)

@router.message(AddBook.author)
async def process_author(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(author=message.text.strip())
    await message.answer(
        "📚 Какой <b>жанр</b> у этой книги?\n"
        "(например: фантастика, детектив, роман, антиутопия...)",
        parse_mode="HTML"
    )
    await state.set_state(AddBook.genre)

@router.message(AddBook.genre)
async def process_genre(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(genre=message.text.strip())
    await message.answer(
        "📅 Укажите <b>год издания</b> (можно пропустить, просто отправьте любое сообщение).",
        parse_mode="HTML"
    )
    await state.set_state(AddBook.year)

@router.message(AddBook.year)
async def process_year(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return

    year = None
    if message.text.isdigit():
        year_num = int(message.text)
        from datetime import datetime
        current_year = datetime.now().year
        if 1450 <= year_num <= current_year + 1:
            year = year_num
        else:
            await message.answer(
                f"📅 Год издания должен быть корректным. Попробуйте снова!",
                "Попробуйте снова или пропустите.",
                parse_mode="HTML"
            )
            return
    # Если не число — пропускаем (оставляем None)
    
    await state.update_data(year=year)
    await message.answer("✨ Книга уже прочитана? Ответьте: <b>да</b> или <b>нет</b>.", parse_mode="HTML")
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
        await message.answer("Пожалуйста, ответьте: <b>да</b> или <b>нет</b>.", parse_mode="HTML")
        return

    await message.answer(
        "🖼️ Отправьте <b>обложку книги</b> (фото) или напишите «пропустить».\n\n"
        "Это сделает вашу библиотеку ещё красивее! ✨",
        parse_mode="HTML"
    )
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
        
        cover_path = str(full_path.relative_to(BASE_DIR))
        await message.answer("✅ Обложка сохранена! Теперь ваша книга выглядит ещё лучше!")
    elif message.text and message.text.strip().lower() == "пропустить":
        await message.answer("⏭️ Хорошо, обложку пропускаем. Всё равно книга будет в вашей коллекции!")
    else:
        await message.answer("Пожалуйста, отправьте фото или напишите «пропустить».")
        return

    await state.update_data(cover_path=cover_path)
    await message.answer(
        "📖 Хотите добавить <b>краткое описание</b> (аннотацию)?\n"
        "Это поможет вам вспомнить сюжет через год! Можно пропустить.",
        parse_mode="HTML"
    )
    await state.set_state(AddBook.description)

@router.message(AddBook.description)
async def process_description(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(description=message.text.strip())
    data = await state.get_data()
    if data["status"] == "read":
        await message.answer(
            "💭 А теперь — самое интересное! Напишите <b>ваши впечатления</b> от книги.\n"
            "Что запомнилось? Что тронуло? Это будет ваша личная рецензия!",
            parse_mode="HTML"
        )
        await state.set_state(AddBook.review)
    else:
        await save_book_to_db(message, state)

@router.message(AddBook.review)
async def process_review(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    await state.update_data(review=message.text.strip())
    await message.answer(
        "⭐ Как бы вы оценили эту книгу по 5-балльной шкале?\n"
        "Отправьте число от 1 до 5."
        # ← Без HTML → без parse_mode
    )
    await state.set_state(AddBook.rating)

@router.message(AddBook.rating)
async def process_rating(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await cancel_handler(message, state)
        return
    if message.text.isdigit() and 1 <= int(message.text) <= 5:
        await state.update_data(rating=int(message.text))
        await message.answer(
            "📆 Когда вы её прочитали? Укажите дату в формате <b>ГГГГ-ММ-ДД</b>\n"
            "Или просто напишите «сегодня» — я сам всё подставлю! 📅",
            parse_mode="HTML"
        )
        await state.set_state(AddBook.date_read)
    else:
        await message.answer("Пожалуйста, введите число от 1 до 5.")

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
            await message.answer("Неверный формат. Используйте ГГГГ-ММ-ДД или «сегодня».")
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
    title = data.get("title", "книга")
    await message.answer(
        f"🎉 Ура! Книга «<b>{title}</b>» успешно добавлена в вашу библиотеку!\n\n"
        "Хотите посмотреть её сейчас? Напишите /my_books",
        parse_mode="HTML"
    )
    await state.clear()

async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Добавление отменено.\n\n"
        "Не переживайте — вы всегда можете начать заново командой /add_book!",
        reply_markup=ReplyKeyboardRemove()
    )