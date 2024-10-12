import asyncio
from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db_pool import get_db_pool
from bot.setup import bot
from bot.start_duel import start_duel

class WeaponCallbackData(CallbackData, prefix="choose_weapon"):
    '''класс для коллбек событий выбора оружия'''
    weapon: str
    user_id: int
    duel_id: int


async def choose_weapon(message: types.Message, duel_info, user_to_choose):
    '''функция для отправки кнопок c выбором оружия'''
    duel_id = duel_info["id"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="♂ Dick",
                    callback_data=WeaponCallbackData(
                        weapon="Dick", user_id=user_to_choose, duel_id=duel_id
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="♂ Ass",
                    callback_data=WeaponCallbackData(
                        weapon="Ass", user_id=user_to_choose, duel_id=duel_id
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="♂ Finger",
                    callback_data=WeaponCallbackData(
                        weapon="Finger", user_id=user_to_choose, duel_id=duel_id
                    ).pack(),
                ),
            ]
        ]
    )

    pool = get_db_pool()
    # забираем username для пинга
    async with pool.acquire() as connection:
        username = await connection.fetchval(
            "SELECT username FROM users WHERE id = $1 AND telegram_group_id = $2",
            user_to_choose,
            message.chat.id,
        )

    sent_message = await message.answer(f"@{username}, выбери оружие:", reply_markup=keyboard)
    message_id = sent_message.message_id

    # обновляем last_message_id в таблице duel_state
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE duel_state SET last_message_id = $1 WHERE id = $2",
            message_id,
            duel_id,
        )


async def weapon_chosen(callback_query: CallbackQuery, callback_data: WeaponCallbackData):
    '''обработчик выбора оружия'''
    telegram_user_id = callback_query.from_user.id
    weapon = callback_data.weapon
    duel_id = callback_data.duel_id
    message = callback_query.message
    chat_id = message.chat.id

    pool = get_db_pool()

    # получаем информацию о дуэли по конкретному duel_id
    async with pool.acquire() as connection:
        duel_info = await connection.fetchrow(
            "SELECT * FROM duel_state WHERE id = $1 AND telegram_group_id = $2",
            duel_id,
            chat_id,
        )

        if not duel_info:
            await callback_query.answer("Дуэль не найдена")
            return

        # получаем внутренний id пользователя по его telegram_id
        user_id = await connection.fetchval(
            "SELECT id FROM users WHERE telegram_id = $1 AND telegram_group_id = $2",
            telegram_user_id,
            chat_id,
        )

        if not user_id:
            await callback_query.answer(
                "Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться."
            )
            return

        # проверяем, кто сейчас должен выбирать оружие
        if (duel_info["challenger_weapon"] is None and user_id == duel_info["challenger_id"]):
            # если вызвавший на дуэль выбирает оружие
            await connection.execute(
                "UPDATE duel_state SET challenger_weapon = $1 WHERE id = $2",
                weapon,
                duel_info["id"],
            )
            await callback_query.answer(f"Ты выбрал {weapon}")

            # удаляем сообщение после выбора оружия первым игроком
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)

            # отправляем новое сообщение для выбора оружия вторым участником
            await choose_weapon(message, duel_info, duel_info["challenged_id"])

        elif (duel_info["challenger_weapon"] is not None and user_id == duel_info["challenged_id"]):
            # если вызванный на дуэль выбирает оружие
            await connection.execute(
                "UPDATE duel_state SET challenged_weapon = $1 WHERE id = $2",
                weapon,
                duel_info["id"],
            )
            await callback_query.answer(f"Ты выбрал {weapon}")

            # удаляем сообщение с кнопками выбора оружия
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)

            # проверка результата дуэли
            winner = determine_winner(duel_info["challenger_weapon"], weapon)

            if winner == "draw":
                # если ничья, сбрасываем выбор оружия
                await connection.execute(
                    """
                    UPDATE duel_state
                    SET challenger_weapon = NULL, challenged_weapon = NULL
                    WHERE id = $1
                    """,
                    duel_info["id"],
                )

                # если ничья, отправляем сообщение и начинаем выбор оружия заново
                draw_message = await bot.send_message(chat_id, "Ничья, ⚣борьба⚣ продолжается")
                
                # удаляем сообщение о ничьей через 2.5 секунд
                await asyncio.sleep(2.5)
                await bot.delete_message(chat_id=chat_id, message_id=draw_message.message_id)

                # начинаем выбор оружия заново
                await choose_weapon(message, duel_info, duel_info["challenger_id"])
            
            else:
                # создаем временное сообщение о начале дуэли
                new_message = await bot.send_message(chat_id, "⚣Борьба⚣ началась!")

                # начинаем дуэль после выбора оружия
                await start_duel(new_message, duel_info, chat_id, winner)

                # удаляем временное сообщение
                await bot.delete_message(chat_id=chat_id, message_id=new_message.message_id)

        else:
            # если это не их очередь выбирать
            await callback_query.answer("Сейчас не твоя очередь выбирать оружие.", show_alert=True)


def determine_winner(challenger_weapon: str, challenged_weapon: str) -> str:
    '''определяет победителя на основе выбранных оружий'''
    if challenger_weapon == challenged_weapon:
        return "draw"

    winning_combinations = {
        "Dick": "Ass",
        "Ass": "Finger",
        "Finger": "Dick",
    }

    if winning_combinations[challenger_weapon] == challenged_weapon:
        return "challenger"
    else:
        return "challenged"