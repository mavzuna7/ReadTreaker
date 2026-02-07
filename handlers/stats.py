# handlers/stats.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from asgiref.sync import sync_to_async
from django.db import models

router = Router()

@sync_to_async
def get_user_stats(telegram_id):
    from books.models import TelegramUser, UserBook
    from django.db import models 
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        
        # Все книги пользователя
        all_books = UserBook.objects.filter(user=user)
        read_books = all_books.filter(status='read')
        want_books = all_books.filter(status='want_to_read')
        
        total_read = read_books.count()
        total_want = want_books.count()
        
        # Средняя оценка
        rated_books = read_books.exclude(rating__isnull=True)
        avg_rating = None
        if rated_books.exists():
            avg_rating = round(
                rated_books.aggregate(avg=models.Avg('rating'))['avg'],
                1
            )
        
        # Последняя прочитанная книга
        last_book = None
        last_ub = read_books.order_by('-date_read').first()
        if last_ub:
            last_book = {
                'title': last_ub.book.title,
                'author': last_ub.book.author,
                'date': last_ub.date_read
            }
        
        # Самый популярный жанр
        top_genre = None
        genre_counts = (
            read_books
            .exclude(book__genre='')
            .values('book__genre')
            .annotate(count=models.Count('book__genre'))
            .order_by('-count')
            .first()
        )
        if genre_counts:
            top_genre = genre_counts['book__genre']
        
        return {
            'total_read': total_read,
            'total_want': total_want,
            'avg_rating': avg_rating,
            'last_book': last_book,
            'top_genre': top_genre
        }
    except Exception as e:
        print("❌ Ошибка статистики:", e)
        return None

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    stats = await get_user_stats(message.from_user.id)
    
    if not stats or (stats['total_read'] == 0 and stats['total_want'] == 0):
        await message.answer("📭 У вас пока нет данных для статистики.")
        return

    text = "📊 <b>Ваша статистика</b>\n\n"
    
    text += f"✅ Прочитано: {stats['total_read']}\n"
    text += f"⏳ Хочу прочитать: {stats['total_want']}\n"
    
    if stats['avg_rating']:
        text += f"⭐ Средняя оценка: {stats['avg_rating']}\n"
    
    if stats['last_book']:
        date_str = str(stats['last_book']['date']) if stats['last_book']['date'] else ""
        text += f"📆 Последняя книга: {stats['last_book']['title']} — {stats['last_book']['author']}"
        if date_str:
            text += f" ({date_str})"
        text += "\n"
    
    if stats['top_genre']:
        text += f"📚 Любимый жанр: {stats['top_genre']}\n"
    
    await message.answer(text, parse_mode="HTML")