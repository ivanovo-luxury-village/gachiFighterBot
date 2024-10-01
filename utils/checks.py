import asyncio 
from datetime import datetime, timedelta, timezone
from utils.logger import logger
from database.db_pool import get_db_pool
from bot.setup import bot

async def check_expired_duels():
    '''функция отвечающая за проверку просроченных дуэлей'''
    pool = get_db_pool()
    while True:
        try:
            current_time = datetime.utcnow() # на dev стенде использовать .now()

            async with pool.acquire() as connection:
                expired_duels = await connection.fetch(
                    """
                    SELECT id
                        , telegram_group_id
                        , last_message_id 
                    FROM duel_state 
                    WHERE status = $1 
                        AND created_at < $2
                    """,
                    "created", 
                    current_time - timedelta(minutes=15)
                )

                for duel in expired_duels:
                    await connection.execute(
                        """
                        UPDATE duel_state 
                        SET status = $1 
                        WHERE id = $2
                        """,
                        "expired (not accepted)",
                        duel['id']
                    )
                    # удаляем сообщение с созданной дуэлью
                    if duel['last_message_id']:
                        try:
                            await bot.delete_message(
                                chat_id=duel['telegram_group_id'], 
                                message_id=duel['last_message_id']
                            )
                            logger.info(f"Deleted message {duel['last_message_id']} for expired duel (not accepted) {duel['id']}")
                        except Exception as e:
                            logger.error(f"Error deleting message for expired (not accepted) duel {duel['id']}: {e}")

                logger.info(f"updated {len(expired_duels)} duel with status 'expired (not accepted)'")
                
        except Exception as e:
            logger.error(f"Error in check_expired_duels: {e}")
        
        await asyncio.sleep(30)  # проверка каждые 30 секунд


async def check_long_in_progress_duels():
    '''функция отвечающая за проверку дуэлей с долгим статусом "in progress"'''
    pool = get_db_pool()
    while True:
        try:
            if pool is None:
                logger.error("Database pool is still not initialized, skipping this iteration")
                await asyncio.sleep(5)  # Подождем перед повторной проверкой
                continue
            
            current_time = datetime.utcnow() # на dev стенде использовать .now()

            async with pool.acquire() as connection:
                long_in_progress_duels = await connection.fetch(
                    """
                    SELECT id
                        , telegram_group_id
                        , last_message_id 
                    FROM duel_state 
                    WHERE status = $1 
                        AND updated_at < $2
                    """,
                    "in progress", 
                    current_time - timedelta(minutes=10)
                )

                for duel in long_in_progress_duels:
                    await connection.execute(
                        """
                        UPDATE duel_state 
                        SET status = $1 
                        WHERE id = $2
                        """,
                        "expired (not finished)",
                        duel['id']
                    )

                    # удаляем сообщение с кнопками
                    if duel['last_message_id']:
                        try:
                            await bot.delete_message(
                                chat_id=duel['telegram_group_id'], 
                                message_id=duel['last_message_id']
                            )
                            logger.info(f"Deleted message {duel['last_message_id']} for expired duel (not finished) {duel['id']}")
                        except Exception as e:
                            logger.error(f"Error deleting message for expired (not finished) duel {duel['id']}: {e}")

                logger.info(f"updated {len(long_in_progress_duels)} duel with status 'expired (not finished)'")
                
        except Exception as e:
            logger.error(f"Error in check_long_in_progress_duels: {e}")
        
        await asyncio.sleep(30)  # проверка каждые 30 секунд


async def check_active_duels(chat_id: int) -> bool:
    '''проверяет количество активных дуэлей'''
    pool = get_db_pool()
    async with pool.acquire() as connection:
        active_duels_count = await connection.fetchval(
            """
            SELECT COUNT(*) 
            FROM duel_state 
            WHERE telegram_group_id = $1 
                AND status IN ('created', 'in progress')
            """,
            chat_id,
        )
    return active_duels_count >= 2


async def check_last_finished_duel(chat_id: int) -> bool:
    '''проверяет время последней завершенной дуэли'''
    pool = get_db_pool()
    async with pool.acquire() as connection:
        last_finished_duel_time = await connection.fetchval(
            """
            SELECT MAX(created_at)
            FROM duel_state 
            WHERE telegram_group_id = $1 
                AND status = 'finished'
            """,
            chat_id,
        )
    
    if last_finished_duel_time:
        current_time = datetime.now(timezone.utc)
        time_since_last_duel = current_time - last_finished_duel_time
        return time_since_last_duel < timedelta(minutes=2)
    
    return False