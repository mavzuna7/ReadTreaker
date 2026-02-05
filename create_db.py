# create_db.py
import psycopg2

try:
    # Подключаемся к стандартной базе 'postgres'
    conn = psycopg2.connect(
        dbname="book_bot_db",
        user="postgres",
        password="123",          # ← замени на свой пароль, если другой
        host="localhost",
        port="5432"
    )
    conn.autocommit = True  # обязательно!
    cursor = conn.cursor()

    # Создаём новую базу
    cursor.execute("CREATE DATABASE book_bot_db;")
    print("✅ База данных 'book_bot_db' успешно создана!")

except psycopg2.errors.DuplicateDatabase:
    print("ℹ️ База данных 'book_bot_db' уже существует.")
except Exception as e:
    print("❌ Ошибка:", e)
finally:
    if 'conn' in locals():
        conn.close()