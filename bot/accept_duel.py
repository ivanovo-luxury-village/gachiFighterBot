from datetime import datetime, timedelta
from aiogram.types import CallbackQuery
from database.db_pool import get_db_pool
from utils.logger import logger
from bot.create_duel import DuelCallbackData
from bot.weapons import choose_weapon


async def callback_accept_duel(query: CallbackQuery, callback_data: DuelCallbackData):
    '''функция для обработки принятия/отклонения дуэли через кнопки'''
    pool = get_db_pool()
    async with pool.acquire() as connection:
        try:
            duel_id = callback_data.id
            chat_id = callback_data.chat_id
            challenged_id = callback_data.challenged_id
            
            user_id = await connection.fetchval(
                "SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2",
                chat_id,
                query.from_user.id,
            )

            if not user_id:
                await query.answer("Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться.", show_alert=True)
                return

            # current_time = datetime.utcnow() # на dev стенде использовать .now()
            current_time = datetime.now()
            
            if callback_data.action == "accept":
                # сценарий 1 & 2: принятие вызова на конкретную дуэль
                if callback_data.duel_type == "specific":
                    duel_info = await connection.fetchrow(
                        """
                        SELECT * 
                        FROM duel_state 
                        WHERE id = $1
                            AND telegram_group_id = $2 
                            AND duel_type = $3
                            AND created_at > $4
                            AND status = $5
                        LIMIT 1
                        """,
                        duel_id,
                        chat_id,
                        "specific",
                        current_time - timedelta(minutes=15),
                        "created"
                    )

                    if not duel_info:
                        await query.answer("Нет доступных дуэлей для принятия", show_alert=True)
                        return

                    if duel_info["challenger_id"] == user_id: #user_id - тот, кто нажимает кнопку
                        await query.answer("Ты не можешь принять бой с самим собой.", show_alert=True)
                        return
                    
                    if duel_info['challenged_id'] != user_id:
                        await query.answer("Ты не можешь принять не свою дуэль.", show_alert=True)

                # сценарий 3: принятие открытой дуэли
                elif callback_data.duel_type == "open":
                    duel_info = await connection.fetchrow(
                        """
                        SELECT * 
                        FROM duel_state 
                        WHERE id = $1
                            AND telegram_group_id = $2
                            AND created_at > $3
                            AND duel_type = $4
                            AND status = $5
                        LIMIT 1
                        """,
                        duel_id,
                        chat_id,
                        current_time - timedelta(minutes=15),
                        "open",
                        "created",
                    )

                    if not duel_info:
                        await query.answer("Нет доступных дуэлей для принятия.", show_alert=True)
                        return

                    if duel_info["challenger_id"] == user_id:
                        await query.answer("Ты не можешь принять бой с самим собой.", show_alert=True)
                        return

                    # обновляем запись, добавляем challenged_id
                    await connection.execute(
                        "UPDATE duel_state SET challenged_id = $1 WHERE telegram_group_id = $2 AND id = $3",
                        user_id,
                        chat_id,
                        duel_id,
                    )

                # обновляем статус дуэли
                await connection.execute(
                    "UPDATE duel_state SET status = $1 WHERE telegram_group_id = $2 AND id = $3",
                    'in progress',
                    chat_id,
                    duel_id,
                )

                # удаляем сообщение о создании дуэли
                await query.message.delete()
                
                # создаем новое сообщение
                message = await query.message.answer("Выбор оружия начался...")
                await choose_weapon(message, duel_info, duel_info["challenger_id"])

            elif callback_data.action == "decline":
                if challenged_id != user_id:
                    await query.answer("Ты не можешь отклонить эту дуэль.", show_alert=True)
                    return

                # логика отклонения дуэли
                await connection.execute(
                    "UPDATE duel_state SET status = 'declined' WHERE id = $1",
                    duel_id
                )
                await query.message.edit_reply_markup(reply_markup=None)
                await query.message.answer("Дуэль отклонена.")

        except Exception as e:
            logger.error(f"Error in callback_accept_duel: {e}")
            await query.message.answer("Произошла ошибка при обработке дуэли.")
            await query.answer("Произошла ошибка при принятии дуэли. Попробуйте еще раз.", show_alert=True)