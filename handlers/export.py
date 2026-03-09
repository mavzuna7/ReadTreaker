# handlers/export.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from asgiref.sync import sync_to_async
import io
from aiogram.types import BufferedInputFile

router = Router()

@sync_to_async
def get_user_books_for_export(telegram_id):
    from books.models import TelegramUser, UserBook
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        books = (
            UserBook.objects
            .filter(user=user)
            .select_related('book')
            .order_by('-status', '-date_read')
        )
        return list(books)
    except Exception as e:
        print("Ошибка экспорта:", e)
        return []

@router.message(Command("export"))
async def cmd_export(message: Message):
    books = await get_user_books_for_export(message.from_user.id)

    if not books:
        await message.answer(
            "📭 Похоже, у вас пока нет книг для экспорта.\n"
            "Добавьте первую командой /add_book!"
        )
        return

    lines = [
        "📚 Моя библиотека — ReadTreakerBot",
        "=" * 50,
        ""
    ]

    for ub in books:
        status_icon = "✅" if ub.status == "read" else "⏳"
        line = f"{status_icon} <b>{ub.book.title}</b> — {ub.book.author}"
        
        details = []
        if ub.book.genre:
            details.append(f"Жанр: {ub.book.genre}")
        if ub.book.year:
            details.append(f"Год: {ub.book.year}")
        if ub.status == "read":
            if ub.rating:
                details.append(f"Оценка: {ub.rating}")
            if ub.date_read:
                details.append(f"Дата: {ub.date_read}")
        if ub.description:
            desc = ub.description[:60] + "..." if len(ub.description) > 60 else ub.description
            details.append(f"Описание: {desc}")
        if ub.review:
            rev = ub.review[:60] + "..." if len(ub.review) > 60 else ub.review
            details.append(f"Рецензия: {rev}")

        if details:
            line += " | " + " | ".join(details)
        
        lines.append(line)

    text = "\n".join(lines)

    # Отправляем как документ
    file_bytes = text.encode('utf-8')
    document = BufferedInputFile(file_bytes, filename="biblioteka.txt")

    await message.answer_document(
        document=document,
        caption="📥 Ваша библиотека успешно экспортирована!\n\n"
                "Теперь вы можете сохранить её на устройстве или распечатать. 📖✨"
    )