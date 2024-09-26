from aiogram import types
from database.db_pool import get_db_pool
from datetime import datetime


async def rating(message: types.Message):
    '''групповой рейтинг пидора дня за актуальный год'''
    pool = get_db_pool()
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
    pool = get_db_pool()

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


async def show_global_fight_stats(message: types.Message):
    '''глобальный рейтинг очков по всем группам'''
    pool = get_db_pool()

    async with pool.acquire() as connection:
        stats = await connection.fetch(
            """
            SELECT 
                users.username
                , SUM(CASE WHEN fight_history.winner_id = users.id THEN 1 ELSE 0 END) AS wins
                , SUM(CASE WHEN fight_history.loser_id = users.id THEN 1 ELSE 0 END) AS losses
                , MAX(COALESCE(user_balance.points, 0)) AS max_balance
            FROM users
            LEFT JOIN fight_history 
                ON (users.id = fight_history.winner_id OR users.id = fight_history.loser_id)
            LEFT JOIN user_balance 
                ON users.id = user_balance.user_id
            GROUP BY users.username
            ORDER BY max_balance DESC
            """
        )

        if not stats:
            await message.reply('Глобальная статистика поединков пока пуста.')
        else:
            stats_message = "Глобальный рейтинг ⚣semen⚣:\n"
            for idx, stat in enumerate(stats, start=1):
                stats_message += (f"{idx}) {stat['username']} - {stat['max_balance']} мл.\n")
            await message.reply(stats_message)
