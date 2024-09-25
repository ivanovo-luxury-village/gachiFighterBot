from aiogram import types
from database.db_pool import get_db_pool

async def register_user(message: types.Message):
    '''регистрация нового пользователя'''
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id

    pool = get_db_pool()
    async with pool.acquire() as connection:
        existing_user = await connection.fetchval(
            "SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2",
            chat_id,
            user_id,
        )
        if existing_user:
            await message.reply("Ты уже зарегистрирован.")
        else:
            new_user_id = await connection.fetchval(
                "INSERT INTO users (telegram_group_id, telegram_id, username) VALUES ($1, $2, $3) RETURNING id",
                chat_id,
                user_id,
                username,
            )
            await connection.execute(
                "INSERT INTO user_balance (telegram_group_id, user_id, points) VALUES ($1, $2, 500)",
                chat_id,
                new_user_id,
            )
            await message.reply("Ты успешно зарегистрирован!")