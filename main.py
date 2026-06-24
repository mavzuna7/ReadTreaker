# main.py
import asyncio
import os
import sys
import django
from pathlib import Path



# === ИНИЦИАЛИЗАЦИЯ DJANGO ===
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booktracker.settings')
django.setup()
# ===========================

import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.add_book import router as add_book_router
from handlers.my_books import router as my_books_router
from handlers.cancel import router as cancel_router
from handlers.delete_book import router as delete_book_router
from handlers.search import router as search_router
from handlers.edit_book import router as edit_book_router
from handlers.stats import router as stats_router
from handlers.export import router as export_router


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    dp.include_router(start_router)
    dp.include_router(add_book_router)
    dp.include_router(my_books_router)
    dp.include_router(cancel_router)
    dp.include_router(delete_book_router)
    dp.include_router(edit_book_router)
    dp.include_router(search_router)
    dp.include_router(stats_router)
    dp.include_router(export_router)
    

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())