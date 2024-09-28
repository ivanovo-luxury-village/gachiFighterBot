from datetime import datetime, timedelta
from aiogram import types
from database.db_pool import get_db_pool
from utils.logger import logger
from bot.weapons import choose_weapon


async def accept_duel_command(message: types.Message):
    '''функция для принятия дуэли'''
    pool = get_db_pool()
    async with pool.acquire() as connection:
        try:
            chat_id = message.chat.id
            user_id = await connection.fetchval(
                "SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2",
                chat_id,
                message.from_user.id,
            )

            if not user_id:
                await message.reply(
                    "Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться."
                )
                return

            current_time = datetime.utcnow()

            # сценарий 1 & 2: принятие вызова на конкретную дуэль (когда пользователь был вызван другим пользователем)
            logger.info("Searching for specific duel where user was challenged.")
            duel_info = await connection.fetchrow(
                """
                SELECT * 
                FROM duel_state 
                WHERE telegram_group_id = $1 
                    AND challenged_id = $2 
                    AND duel_type = $3 
                    AND created_at > $4
                    AND status = $5
                LIMIT 1
                """,
                chat_id,
                user_id,
                "specific",
                current_time - timedelta(minutes=15),
                "created"
            )

            # если пользователь вызван на конкретную дуэль
            if duel_info:
                logger.info("Specific duel found, accepting")

                # проверка: нельзя принять дуэль, созданную самим собой
                if duel_info["challenger_id"] == user_id:
                    await message.reply("Ты не можешь принять бой с самим собой.")
                    return

                # здесь мы не обновляем challenged_id, так как оно уже установлено в вызове дуэли

            # сценарий 3: принятие открытой дуэли
            else:
                logger.info("No specific duel found, searching for open duel.")
                duel_info = await connection.fetchrow(
                    """
                    SELECT * 
                    FROM duel_state 
                    WHERE telegram_group_id = $1 
                        AND challenged_id IS NULL 
                        AND created_at > $2 
                        AND duel_type = $3
                        AND status = $4
                    LIMIT 1
                    """,
                    chat_id,
                    current_time - timedelta(minutes=15),
                    "open",
                    "created"
                )

                if not duel_info:
                    await message.reply("Нет доступных дуэлей для принятия.")
                    return

                # проверка: нельзя принять открытую дуэль от самого себя
                if duel_info["challenger_id"] == user_id:
                    await message.reply("Ты не можешь принять бой с самим собой.")
                    return

                # обновляем запись, добавляем challenged_id
                await connection.execute(
                    "UPDATE duel_state SET challenged_id = $1 WHERE telegram_group_id = $2 AND id = $3",
                    user_id,
                    chat_id,
                    duel_info["id"],
                )

            # обновляем статус дуэли
            await connection.execute(
                "UPDATE duel_state SET status = $1 WHERE telegram_group_id = $2 AND id = $3",
                'in progress',
                chat_id,
                duel_info["id"],
            )

            # начинаем выбор оружия с вызвавшего на дуэль
            await choose_weapon(message, duel_info, duel_info["challenger_id"])

        except Exception as e:
            logger.error(f"Error in accept_duel_command: {e}")
            await message.reply(
                "Произошла ошибка при принятии дуэли. Попробуйте еще раз."
            )
