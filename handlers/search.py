# handlers/search.py
from aiogram import Router
from aiogram.types import ReplyKeyboardRemove, Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async

router = Router()

class SearchBooks(StatesGroup):
    selecting_field = State()
    entering_query = State()
    viewing_results = State()

@sync_to_async
def search_books_by_field(telegram_id, field, query):
    from books.models import TelegramUser, UserBook
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        if field == "title":
            books = list(UserBook.objects.filter(user=user, book__title__icontains=query).select_related('book'))
        elif field == "author":
            books = list(UserBook.objects.filter(user=user, book__author__icontains=query).select_related('book'))
        elif field == "genre":
            books = list(UserBook.objects.filter(user=user, book__genre__icontains=query).select_related('book'))
        else:
            books = []
        return books
    except:
        return []

@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="По названию")],
            [KeyboardButton(text="По автору")],
            [KeyboardButton(text="По жанру")],
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "🔍 <b>Как будем искать?</b>\n\n"
        "Выберите поле для поиска:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.set_state(SearchBooks.selecting_field)

@router.message(SearchBooks.selecting_field)
async def process_select_field(message: Message, state: FSMContext):
    if message.text == "Отмена" or message.text == "/cancel":
        await state.clear()
        await message.answer(
            "⏹️ Поиск отменён.\n\n"
            "Все ваши книги на месте! 📚",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    field_map = {
        "По названию": "title",
        "По автору": "author",
        "По жанру": "genre"
    }

    if message.text not in field_map:
        await message.answer("Пожалуйста, выберите вариант из меню.")
        return

    field = field_map[message.text]
    await state.update_data(search_field=field)
    
    label = message.text.replace("По ", "").lower()
    await message.answer(
        f"💬 Введите ключевое слово для поиска <b>{label}</b>:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(SearchBooks.entering_query)

@router.message(SearchBooks.entering_query)
async def process_query(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "⏹️ Поиск отменён.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    query = message.text.strip()
    if not query:
        await message.answer("Пожалуйста, введите непустой запрос.")
        return

    data = await state.get_data()
    field = data["search_field"]

    books = await search_books_by_field(message.from_user.id, field, query)

    if not books:
        await message.answer(
            "🤔 Ничего не найдено по запросу «<b>{}</b>».\n\n"
            "💡 Попробуйте уточнить название, фамилию автора или жанр.".format(query),
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return

    text = f"✨ Найдено <b>{len(books)}</b> книга(и) по запросу «<b>{query}</b>»:\n\n"
    for i, ub in enumerate(books, 1):
        status_icon = "✅" if ub.status == "read" else "⏳"
        rating = f" ⭐{ub.rating}" if ub.rating else ""
        date = f" ({ub.date_read})" if ub.date_read else ""
        text += f"{i}. {status_icon} <b>{ub.book.title}</b> — {ub.book.author}{rating}{date}\n"

    text += "\n📖 Отправьте <b>номер</b> книги, чтобы посмотреть подробности.\n"
    text += "❌ Или напишите /cancel, чтобы выйти."

    await message.answer(text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await state.update_data(found_books=[b.id for b in books])
    await state.set_state(SearchBooks.viewing_results)

@router.message(SearchBooks.viewing_results)
async def process_view_result(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "⏹️ Просмотр результатов отменён.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите <b>номер</b> из списка.", parse_mode="HTML")
        return

    data = await state.get_data()
    book_ids = data.get("found_books", [])
    num = int(message.text)

    if num < 1 or num > len(book_ids):
        await message.answer(
            f"Введите число от <b>1 до {len(book_ids)}</b>.",
            parse_mode="HTML"
        )
        return

    @sync_to_async
    def get_full_book(book_id):
        from books.models import UserBook
        return UserBook.objects.select_related('book').get(id=book_id)

    ub = await get_full_book(book_ids[num - 1])

    # Формируем карточку
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
            from aiogram.types import FSInputFile
            photo = FSInputFile(cover_path)
            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode="HTML"
            )
            await state.clear()
            return
        except Exception as e:
            print(f"❌ Ошибка отправки обложки в поиске: {e}")

    await message.answer(text, parse_mode="HTML")
    await state.clear()