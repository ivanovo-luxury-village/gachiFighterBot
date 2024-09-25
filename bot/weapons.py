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

    # редактируем или отправляем сообщение для выбора
    if message.reply_markup:
        await message.edit_text(f"@{username}, выбери оружие:", reply_markup=keyboard)
    else:
        await message.answer(f"@{username}, выбери оружие:", reply_markup=keyboard)



async def weapon_chosen(
    callback_query: CallbackQuery, callback_data: WeaponCallbackData
):
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
        if (
            duel_info["challenger_weapon"] is None
            and user_id == duel_info["challenger_id"]
        ):
            # если вызвавший на дуэль выбирает оружие
            await connection.execute(
                "UPDATE duel_state SET challenger_weapon = $1 WHERE id = $2",
                weapon,
                duel_info["id"],
            )
            await callback_query.answer(f"Ты выбрал {weapon}")
            await choose_weapon(message, duel_info, duel_info["challenged_id"])

        elif (
            duel_info["challenger_weapon"] is not None
            and user_id == duel_info["challenged_id"]
        ):
            # если вызванный на дуэль выбирает оружие
            await connection.execute(
                "UPDATE duel_state SET challenged_weapon = $1 WHERE id = $2",
                weapon,
                duel_info["id"],
            )
            await callback_query.answer(f"Ты выбрал {weapon}")

            # создаем новое сообщение о начале дуэли
            new_message = await bot.send_message(chat_id, "Борьба началась!")

            # удаляем сообщение с кнопками выбора оружия
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)

            # начинаем дуэль после выбора оружия
            await start_duel(new_message, duel_info, user_id, chat_id)

        else:
            # если это не их очередь выбирать
            await callback_query.answer(
                "Сейчас не твоя очередь выбирать оружие.", show_alert=True
            )