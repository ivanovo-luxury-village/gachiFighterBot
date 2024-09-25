import asyncio 
from datetime import datetime, timedelta
from utils.logger import logger
from database.db_pool import get_db_pool


async def check_expired_duels():
    '''функция отвечающая за проверку просроченных дуэлей'''
    pool = get_db_pool()
    while True:
        try:
            current_time = datetime.utcnow()

            async with pool.acquire() as connection:
                expired_duels = await connection.fetch(
                    """
                    SELECT id 
                    FROM duel_state 
                    WHERE status = $1 
                        AND created_at < $2
                    """,
                    "created", 
                    current_time - timedelta(minutes=5)
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
            
            current_time = datetime.utcnow()

            async with pool.acquire() as connection:
                long_in_progress_duels = await connection.fetch(
                    """
                    SELECT id 
                    FROM duel_state 
                    WHERE status = $1 
                        AND created_at < $2
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
                logger.info(f"updated {len(long_in_progress_duels)} duel with status 'expired (not finished)'")
                
        except Exception as e:
            logger.error(f"Error in check_long_in_progress_duels: {e}")
        
        await asyncio.sleep(30)  # проверка каждые 30 секунд