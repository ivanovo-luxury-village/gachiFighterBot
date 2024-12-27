from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db_pool import get_db_pool


class DebtRequestCallbackData(CallbackData, prefix="debt_request"):
    action: str
    user_id: int  # используем внутренний ID из таблицы users

class DebtAmountCallbackData(CallbackData, prefix="debt_amount"):
    amount: int
    creditor_id: int  # внутренний ID кредитора
    debtor_id: int  # внутренний ID должника

async def request_debt(message: types.Message):
    pool = get_db_pool()

    # извлекаем внутренний ID пользователя из базы
    async with pool.acquire() as connection:
        debtor_id = await connection.fetchval(
            "SELECT id FROM users WHERE telegram_id = $1",
            message.from_user.id,
        )

    if not debtor_id:
        await message.reply("Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться.")
        return

    # Кнопка "Дать в долг"
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Дать в долг",
                    callback_data=DebtRequestCallbackData(action="give_debt", user_id=debtor_id).pack()
                )
            ]
        ]
    )

    await message.answer(f"@{message.from_user.username} просит дать ему в долг ⚣semen⚣. Кто готов выручить этого бедолагу?", reply_markup=buttons)

async def handle_debt_request(callback_query: CallbackQuery, callback_data: DebtRequestCallbackData):
    pool = get_db_pool()
    creditor_telegram_id = callback_query.from_user.id

    # извлекаем внутренние ID кредитора и должника
    async with pool.acquire() as connection:
        creditor_id = await connection.fetchval(
            "SELECT id FROM users WHERE telegram_id = $1",
            creditor_telegram_id,
        )
        debtor_id = callback_data.user_id

    if not creditor_id:
        await callback_query.answer("Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться.")
        return

    if creditor_id == debtor_id:
        await callback_query.answer("Ты не можешь дать в долг самому себе!", show_alert=True)
        return

    # кнопки выбора суммы долга
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="100", callback_data=DebtAmountCallbackData(amount=100, creditor_id=creditor_id, debtor_id=debtor_id).pack())],
            [InlineKeyboardButton(text="250", callback_data=DebtAmountCallbackData(amount=250, creditor_id=creditor_id, debtor_id=debtor_id).pack())],
            [InlineKeyboardButton(text="500", callback_data=DebtAmountCallbackData(amount=500, creditor_id=creditor_id, debtor_id=debtor_id).pack())],
            [InlineKeyboardButton(text="1000", callback_data=DebtAmountCallbackData(amount=1000, creditor_id=creditor_id, debtor_id=debtor_id).pack())],
        ]
    )

    await callback_query.message.edit_text("Выбери сумму:", reply_markup=buttons)

async def handle_debt_amount(callback_query: CallbackQuery, callback_data: DebtAmountCallbackData):
    creditor_id = callback_data.creditor_id  # внутренний ID кредитора
    debtor_id = callback_data.debtor_id  # внутренний ID должника
    amount = callback_data.amount

    # Получаем внутренний ID пользователя из базы для проверки
    pool = get_db_pool()
    async with pool.acquire() as connection:
        current_user_id = await connection.fetchval(
            "SELECT id FROM users WHERE telegram_id = $1",
            callback_query.from_user.id,
        )

    # проверяем, что текущий пользователь является кредитором
    if current_user_id != creditor_id:
        await callback_query.answer("Эту кнопку может нажимать только тот, кто решил дать в долг!", show_alert=True)
        return

    # записываем долг в базу
    async with pool.acquire() as connection:
        await connection.execute(
            """
            INSERT INTO debts (telegram_group_id, debtor_id, creditor_id, debt_sum, status)
            VALUES ($1, $2, $3, $4, $5)
            """,
            callback_query.message.chat.id,
            debtor_id,
            creditor_id,
            amount,
            "pending"
        )

        # снимаем сумму с баланса кредитора
        await connection.execute("""
            UPDATE user_balance
            SET points = points - $1
            WHERE telegram_group_id = $2
                AND user_id = $3
            """,
            amount,
            callback_query.message.chat.id,
            creditor_id,
        )

        # зачисляем сумму на баланс должнику
        await connection.execute("""
            UPDATE user_balance
            SET points = points + $1
            WHERE telegram_group_id = $2
                AND user_id = $3
            """,
            amount,
            callback_query.message.chat.id,
            debtor_id,
        )

    await callback_query.message.edit_text(f"Долг на сумму {amount} ⚣semen⚣ успешно создан!")