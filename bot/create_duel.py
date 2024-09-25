import os
import random
from datetime import datetime, timedelta, timezone
from aiogram import types
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
from database.db_pool import get_db_pool
from utils.logger import logger
from bot.setup import bot


async def duel_command(message: types.Message):
    '''функция отвечающая за дуэли'''
    pool = get_db_pool()
    async with pool.acquire() as connection:
        try:
            chat_id = message.chat.id
            challenger_id = await connection.fetchval(
                "SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2",
                chat_id,
                message.from_user.id,
            )
            logger.info(f"Challenger ID: {challenger_id}")

            if not challenger_id:
                await message.reply(
                    "Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться."
                )
                return

            # cooldown 1: если есть 2 дуэли со статусами 'created' или 'in progress'
            active_duels_count = await connection.fetchval(
                """
                SELECT COUNT(*) 
                FROM duel_state 
                WHERE telegram_group_id = $1 
                    AND status IN ('created', 'in progress')
                """,
                chat_id,
            )

            if active_duels_count >= 2:
                await message.reply(
                    "Пока ⚣побороться⚣ не получится, подожди пока закончатся текущие бои."
                )
                return
            
            # cooldown 2: если прошло менее 3 минут с последней дуэли 'finished'
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
                if time_since_last_duel < timedelta(minutes=3):
                    await message.reply(
                        "Нужен перерыв между ⚣борьбой⚣, попробуй через пару минут"
                    )
                    return

            challenged_id = None
            mentioned_username = None

            # сценарий 1: ответ на сообщение
            if message.reply_to_message:
                logger.info("Reply to message found.")
                challenged_id = await connection.fetchval(
                    "SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2",
                    chat_id,
                    message.reply_to_message.from_user.id,
                )
                logger.info(f"Challenged ID from reply: {challenged_id}")

                if not challenged_id:
                    await message.reply(
                        "Пользователь, которому ты бросил вызов, не зарегистрирован."
                    )
                    logger.info("Challenged user is not registered.")
                    return

                # проверка, чтобы пользователь не мог вызвать сам себя на дуэль
                if challenger_id == challenged_id:
                    await message.reply("Ты не можешь вызвать на бой самого себя.")
                    return

                await message.reply(
                    f"@{message.reply_to_message.from_user.username}, *тебе бросили вызов*\! Поборешься с этим ♂jabroni♂\? \(/accept\)",
                    parse_mode=ParseMode.MARKDOWN_V2,
                )

            # сценарий 2: упоминание другого пользователя
            elif len(message.text.split()) > 1:
                mentioned_username = message.text.split()[1].strip("@")
                challenged_id = await connection.fetchval(
                    "SELECT id FROM users WHERE telegram_group_id = $1 AND username = $2",
                    chat_id,
                    mentioned_username,
                )
                logger.info(f"Challenged ID from mention: {challenged_id}")

                if not challenged_id:
                    await message.reply(
                        f"Пользователь @{mentioned_username} не зарегистрирован."
                    )
                    return

                # проверка, чтобы пользователь не мог вызвать сам себя на дуэль
                if challenger_id == challenged_id:
                    await message.reply("Ты не можешь вызвать на бой самого себя.")
                    return

                await message.reply(
                    f"@{mentioned_username}, *тебе бросили вызов*\! Поборешься с этим ♂jabroni♂\? \(/accept\)",
                    parse_mode=ParseMode.MARKDOWN_V2,
                )

            # сценарий 3: открытая дуэль
            else:
                logger.info("Open duel created.")

                imgs_folder_path = "./media/pics"
                all_imgs = [
                    os.path.join(imgs_folder_path, file)
                    for file in os.listdir(imgs_folder_path)
                    if file.endswith(".jpg")
                ]
                image_path = random.sample(all_imgs, 1)[0]

                image = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=image,
                    caption="Я новый *♂dungeon master♂*\! Кто не согласен, отзовись или молчи вечно\! /accept\.",
                    parse_mode="MarkdownV2",
                )

                result = await connection.execute(
                    """
                    INSERT INTO duel_state (challenger_id, challenged_id, duel_type, telegram_group_id, status) 
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    challenger_id,
                    None,
                    "open",
                    chat_id,
                    "created"
                )
                logger.info(f"Open Duel Insert Result: {result}")
                return

            # добавление дуэли в базу (кроме открытой дуэли)
            if challenged_id is not None:
                result = await connection.execute(
                    """
                    INSERT INTO duel_state (challenger_id, challenged_id, duel_type, telegram_group_id, status) 
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    challenger_id,
                    challenged_id,
                    "specific",
                    chat_id,
                    "created"
                )
                logger.info(f"Duel Insert Result: {result}")

        except Exception as e:
            logger.error(f"Error in duel_command: {e}")
            await message.reply(
                "Произошла ошибка при создании дуэли. Попробуй еще раз."
            )