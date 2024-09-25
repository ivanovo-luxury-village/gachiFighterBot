import random
from aiogram import types
from datetime import datetime
from database.db_pool import get_db_pool
from aiogram.enums import ParseMode
from utils.service_funcs import send_messages_with_delay

async def choose_pidor_of_the_day(message: types.Message):
    '''функция выбора пидора дня'''
    today = datetime.utcnow().date()
    chat_id = message.chat.id
    current_year = today.year

    pool = get_db_pool()
    async with pool.acquire() as connection:
        fighter_today = await connection.fetchrow(
            "SELECT user_id FROM pidor_of_the_day WHERE telegram_group_id = $1 AND chosen_at = $2",
            chat_id,
            today,
        )

        if fighter_today:
            user = await connection.fetchrow(
                "SELECT username FROM users WHERE telegram_group_id = $1 AND id = $2",
                chat_id,
                fighter_today["user_id"],
            )
            await message.reply(
                f'Согласно моей информации, по результатам сегодняшнего розыгрыша *пидор* дня: @{user["username"]}',
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        else:
            users = await connection.fetch(
                "SELECT id, username FROM users WHERE telegram_group_id = $1", chat_id
            )
            if not users:
                await message.reply("Нет зарегистрированных пользователей.")
                return

            chosen_user = random.choice(users)
            await connection.execute(
                "INSERT INTO pidor_of_the_day (user_id, chosen_at, chosen_year, telegram_group_id) VALUES ($1, $2, $3, $4)",
                chosen_user["id"],
                today,
                current_year,
                chat_id,
            )
            await connection.execute(
                "INSERT INTO statistics (user_id, chosen_count, chosen_year, telegram_group_id) VALUES ($1, 1, $2, $3) ON CONFLICT (user_id, chosen_year, telegram_group_id) DO UPDATE SET chosen_count = statistics.chosen_count + 1",
                chosen_user["id"],
                current_year,
                chat_id,
            )

            scenario_id = await connection.fetchval(
                "SELECT scenario_id FROM (SELECT DISTINCT scenario_id FROM messages WHERE message_type = $1) AS subquery ORDER BY random() LIMIT 1",
                "INIT",
            )
            messages = await connection.fetch(
                "SELECT message_text FROM messages WHERE message_type = $1 AND scenario_id = $2 ORDER BY message_order",
                "INIT",
                scenario_id,
            )
            message_texts = [record["message_text"] for record in messages]
            await send_messages_with_delay(message.chat.id, message_texts, 2)

            # выбор случайного сообщения типа RESULT и вставка имени пользователя
            result_message_template = await connection.fetchval(
                "SELECT message_text FROM messages WHERE message_type = $1 ORDER BY random() LIMIT 1",
                "RESULT",
            )
            result_message = result_message_template.replace(
                "{username}", f'@{chosen_user["username"]}'
            )
            await message.reply(result_message)