# handlers/recommend.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from asgiref.sync import sync_to_async
import random

router = Router()

@sync_to_async
def get_recommendation(telegram_id):
    from books.models import TelegramUser, UserBook, Book
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        
        # Получаем все прочитанные книги пользователя
        read_books = UserBook.objects.filter(user=user, status='read').select_related('book')
        if not read_books.exists():
            return None, "Вы ещё не прочитали ни одной книги."

        # Собираем жанры
        genres = [ub.book.genre for ub in read_books if ub.book.genre]
        if not genres:
            return None, "В прочитанных книгах не указаны жанры."

        # Находим самый частый жанр
        from collections import Counter
        most_common_genre = Counter(genres).most_common(1)[0][0]

        # Получаем ID всех книг пользователя (чтобы исключить)
        user_book_ids = UserBook.objects.filter(user=user).values_list('book_id', flat=True)

        # Ищем книги в этом жанре, которых нет у пользователя
        candidates = list(
            Book.objects.filter(genre=most_common_genre)
            .exclude(id__in=user_book_ids)
        )

        if not candidates:
            return None, f"Нет новых книг в жанре «{most_common_genre}»."

        # Выбираем случайную
        recommended = random.choice(candidates)
        return recommended, f"Ваш любимый жанр: {most_common_genre}"
    
    except Exception as e:
        print("Ошибка рекомендации:", e)
        return None, "Не удалось сгенерировать рекомендацию."

@router.message(Command("recommend"))
async def cmd_recommend(message: Message):
    book, info = await get_recommendation(message.from_user.id)
    
    if book is None:
        await message.answer(f"📭 {info}")
        return

    text = f"💡 <b>Рекомендую прочитать:</b>\n\n"
    text += f"📘 <b>{book.title}</b>\n"
    text += f"✍️ {book.author}\n"
    if book.genre:
        text += f"📚 Жанр: {book.genre}\n"
    if book.year:
        text += f"📅 Год: {book.year}\n"

    # Отправляем обложку, если есть
    if book.cover_path:
        import os
        from pathlib import Path
        BASE_DIR = Path(__file__).resolve().parent.parent
        full_path = BASE_DIR / book.cover_path
        if full_path.exists():
            try:
                with open(full_path, 'rb') as photo:
                    await message.answer_photo(photo, caption=text, parse_mode="HTML")
                return
            except:
                pass

    await message.answer(text, parse_mode="HTML")