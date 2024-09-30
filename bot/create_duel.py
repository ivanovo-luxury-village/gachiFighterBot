import os
import random
from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from database.db_pool import get_db_pool
from utils.logger import logger
from utils.checks import check_active_duels, check_last_finished_duel
from bot.setup import bot


class DuelCallbackData(CallbackData, prefix="duel"):
    id: int
    action: str
    challenger_id: int
    challenged_id: int | None
    chat_id: int
    duel_type: str


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

            if not challenger_id:
                await message.reply(
                    "Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться."
                )
                return

            # проверка на активные дуэли
            if await check_active_duels(chat_id):
                await message.reply(
                    "Пока ⚣побороться⚣ не получится, подожди завершения текущих боев."
                )
                return
            
            # проверка на время последней завершенной дуэли
            if await check_last_finished_duel(chat_id):
                await message.reply(
                    "Нужен перерыв между ⚣борьбой⚣, попробуй через пару минут"
                )
                return

            challenged_id = None
            mentioned_username = None
            duel_id = None
            message_id = None

            # сценарий 1: ответ на сообщение
            if message.reply_to_message:
                challenged_id = await connection.fetchval(
                    "SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2",
                    chat_id,
                    message.reply_to_message.from_user.id,
                )

                if not challenged_id:
                    await message.reply(
                        "Пользователь, которому ты бросил вызов, не зарегистрирован."
                    )
                    return

                # проверка, чтобы пользователь не мог вызвать сам себя на дуэль
                if challenger_id == challenged_id:
                    await message.reply("Ты не можешь вызвать на бой самого себя.")
                    return

                duel_id = await connection.fetchval(
                    """
                    INSERT INTO duel_state (challenger_id, challenged_id, duel_type, telegram_group_id, status) 
                    VALUES ($1, $2, $3, $4, $5) RETURNING id
                    """,
                    challenger_id,
                    challenged_id,
                    "specific",
                    chat_id,
                    "created",
                )

                # вызов кнопок принять / отклонить 
                buttons = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Принять",
                                callback_data=DuelCallbackData(
                                    id=duel_id,
                                    action="accept",
                                    challenger_id=challenger_id,
                                    challenged_id=challenged_id,
                                    chat_id=chat_id,
                                    duel_type="specific"
                                ).pack(),
                            ),
                            InlineKeyboardButton(
                                text="Отклонить",
                                callback_data=DuelCallbackData(
                                    id=duel_id,
                                    action="decline",
                                    challenger_id=challenger_id,
                                    challenged_id=challenged_id,
                                    chat_id=chat_id,
                                    duel_type="specific"
                                ).pack(),
                            ),
                        ]
                    ]
                )

                sent_message = await message.reply(
                    f"@{message.reply_to_message.from_user.username}, тебе бросили вызов! Поборешься с этим ♂jabroni♂?",
                    reply_markup=buttons
                )
                message_id = sent_message.message_id

                # обновляем last_message_id в таблице duel_state
                await connection.execute(
                    "UPDATE duel_state SET last_message_id = $1 WHERE id = $2",
                    message_id,
                    duel_id,
                )

            # сценарий 2: упоминание другого пользователя
            elif len(message.text.split()) > 1:
                mentioned_username = message.text.split()[1].strip("@")
                challenged_id = await connection.fetchval(
                    "SELECT id FROM users WHERE telegram_group_id = $1 AND username = $2",
                    chat_id,
                    mentioned_username,
                )

                if not challenged_id:
                    await message.reply(
                        f"Пользователь @{mentioned_username} не зарегистрирован."
                    )
                    return

                # проверка, чтобы пользователь не мог вызвать сам себя на дуэль
                if challenger_id == challenged_id:
                    await message.reply("Ты не можешь вызвать на бой самого себя.")
                    return

                duel_id = await connection.fetchval(
                    """
                    INSERT INTO duel_state (challenger_id, challenged_id, duel_type, telegram_group_id, status) 
                    VALUES ($1, $2, $3, $4, $5) RETURNING id
                    """,
                    challenger_id,
                    challenged_id,
                    "specific",
                    chat_id,
                    "created",
                )

                # вызов кнопок принять / отклонить 
                buttons = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Принять",
                                callback_data=DuelCallbackData(
                                    id=duel_id,
                                    action="accept",
                                    challenger_id=challenger_id,
                                    challenged_id=challenged_id,
                                    chat_id=chat_id,
                                    duel_type="specific"
                                ).pack(),
                            ),
                            InlineKeyboardButton(
                                text="Отклонить",
                                callback_data=DuelCallbackData(
                                    id=duel_id,
                                    action="decline",
                                    challenger_id=challenger_id,
                                    challenged_id=challenged_id,
                                    chat_id=chat_id,
                                    duel_type="specific"
                                ).pack(),
                            ),
                        ]
                    ]
                )

                sent_message = await message.reply(
                    f"@{mentioned_username}, тебе бросили вызов! Поборешься с этим ♂jabroni♂?",
                    reply_markup=buttons
                )
                message_id = sent_message.message_id

                # обновляем last_message_id в таблице duel_state
                await connection.execute(
                    "UPDATE duel_state SET last_message_id = $1 WHERE id = $2",
                    message_id,
                    duel_id,
                )

            # сценарий 3: открытая дуэль
            else:
                imgs_folder_path = "./media/pics"
                all_imgs = [
                    os.path.join(imgs_folder_path, file)
                    for file in os.listdir(imgs_folder_path)
                    if file.endswith(".jpg")
                ]
                image_path = random.sample(all_imgs, 1)[0]

                image = FSInputFile(image_path)
                challenger_username = await connection.fetchval(
                    "SELECT username FROM users WHERE telegram_group_id = $1 AND id = $2",
                    chat_id,
                    challenger_id
                )

                duel_id = await connection.fetchval(
                    """
                    INSERT INTO duel_state (challenger_id, challenged_id, duel_type, telegram_group_id, status) 
                    VALUES ($1, $2, $3, $4, $5) RETURNING id
                    """,
                    challenger_id,
                    None,
                    "open",
                    chat_id,
                    "created",
                )
                
                # вызов кнопки для принятия 
                buttons = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Принять",
                                callback_data=DuelCallbackData(
                                    id=duel_id,
                                    action="accept",
                                    challenger_id=challenger_id,
                                    challenged_id=None,
                                    chat_id=chat_id,
                                    duel_type="open"
                                ).pack(),
                            ),
                        ]
                    ]
                )

                sent_message = await bot.send_photo(
                    chat_id=chat_id,
                    photo=image,
                    caption="@"+challenger_username+": Я новый ⚣dungeon master⚣! Кто не согласен, отзовись или молчи вечно!",
                    reply_markup=buttons
                )
                message_id = sent_message.message_id

                # обновляем last_message_id в таблице duel_state
                await connection.execute(
                    "UPDATE duel_state SET last_message_id = $1 WHERE id = $2",
                    message_id,
                    duel_id,
                )

        except Exception as e:
            logger.error(f"Error in duel_command: {e}")