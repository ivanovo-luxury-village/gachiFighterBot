from aiogram import types
from database.db_pool import create_db_pool, pool
from datetime import datetime

async def rating(message: types.Message):
    '''групповой рейтинг пидора дня за актуальный год'''
    await create_db_pool()
    current_year = datetime.utcnow().year
    chat_id = message.chat.id

    async with pool.acquire() as connection:
        stats = await connection.fetch(
            """
            SELECT 
                users.username
                , COALESCE(statistics.chosen_count, 0) AS chosen_count
            FROM users
            LEFT JOIN statistics 
                ON users.id = statistics.user_id 
                    AND users.telegram_group_id = statistics.telegram_group_id
                    AND statistics.chosen_year = $1
            WHERE 1=1
                AND users.telegram_group_id = $2
            ORDER BY chosen_count DESC
            """,
            current_year,
            chat_id,
        )

        if not stats:
            await message.reply("Статистика пока пуста.")
        else:
            stats_message = (
                f"Рейтинг пидоров (данные актуальны на {current_year} год):\n"
            )
            for idx, stat in enumerate(stats, start=1):
                stats_message += (
                    f"{idx}. {stat['username']}: {stat['chosen_count']} раз\n"
                )
            await message.reply(stats_message)


async def show_fight_stats(message: types.Message):
    '''групповой рейтинг очков'''
    await create_db_pool()

    chat_id = message.chat.id

    async with pool.acquire() as connection:
        stats = await connection.fetch(
            """
            SELECT 
                users.username
                , COUNT(CASE WHEN fight_history.winner_id = users.id THEN 1 END) AS wins
                , COUNT(CASE WHEN fight_history.loser_id = users.id THEN 1 END) AS losses
                , COALESCE(user_balance.points, 0) AS current_balance
            FROM users
            LEFT JOIN fight_history 
                ON (users.id = fight_history.winner_id OR users.id = fight_history.loser_id)
                    AND users.telegram_group_id = fight_history.telegram_group_id
            LEFT JOIN user_balance 
                ON users.id = user_balance.user_id
                    AND users.telegram_group_id = user_balance.telegram_group_id
            WHERE 1=1
                AND users.telegram_group_id = $1
            GROUP BY users.username, user_balance.points
            ORDER BY current_balance DESC
            """,
            chat_id,
        )

        if not stats:
            await message.reply('Статистика поединков пока пуста.')
        else:
            stats_message = "Групповой рейтинг ⚣semen⚣:\n"
            for idx, stat in enumerate(stats, start=1):
                stats_message += (f"{idx}) {stat['username']} - {stat['current_balance']} мл.\n")
            await message.reply(stats_message)