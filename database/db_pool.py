import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

# настройки подключения к базе данных
DB_HOST = os.getenv("POSTGRES_DB_HOST")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PORT = os.getenv("POSTGRES_PORT")

pool = None

# функция для подключения к базе данных
async def create_db_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT,
        )