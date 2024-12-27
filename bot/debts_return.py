from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db_pool import get_db_pool

class ReturnDebtUserCallbackData(CallbackData, prefix="return_debt_user"):
    creditor_id: int
    debtor_id: int

class ReturnDebtAmountCallbackData(CallbackData, prefix="return_debt_amount"):
    debt_id: int
    debtor_id: int

class ReturnDebtNavigationCallbackData(CallbackData, prefix="return_debt_nav"):
    action: str  # "back" or other actions

async def return_debt(message: types.Message):
    pool = get_db_pool()

    async with pool.acquire() as connection:
        # проверяем, есть ли у пользователя долги
        debtor_id = await connection.fetchval(
            """
            SELECT id
            FROM users
            WHERE telegram_id = $1
              AND telegram_group_id = $2
            """,
            message.from_user.id,
            message.chat.id,
        )

        if not debtor_id:
            await message.reply("Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться.")
            return

        debts = await connection.fetch(
            """
            SELECT DISTINCT creditor_id
            FROM debts
            WHERE debtor_id = $1
              AND telegram_group_id = $2
              AND status = 'pending'
            """,
            debtor_id,
            message.chat.id,
        )

        if not debts:
            await message.reply("У тебя нет долгов, которые нужно вернуть.")
            return

        # формируем список кредиторов
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"{creditor['creditor_id']}",  # позже можно заменить на username
                    callback_data=ReturnDebtUserCallbackData(
                        creditor_id=creditor["creditor_id"],
                        debtor_id=debtor_id
                    ).pack()
                )
            ]
            for creditor in debts
        ]
        buttons.append([
            InlineKeyboardButton(text="Отмена", callback_data=ReturnDebtNavigationCallbackData(action="back").pack())
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.reply("Выбери, кому ты хочешь вернуть долг:", reply_markup=keyboard)

async def handle_return_debt_user(callback_query: CallbackQuery, callback_data: ReturnDebtUserCallbackData):
    pool = get_db_pool()

    async with pool.acquire() as connection:
        # проверяем, что запрос делает тот, кто должен вернуть долг
        current_user_id = await connection.fetchval(
            """
            SELECT id
            FROM users
            WHERE telegram_id = $1
              AND telegram_group_id = $2
            """,
            callback_query.from_user.id,
            callback_query.message.chat.id,
        )

        if current_user_id != callback_data.debtor_id:
            await callback_query.answer("Только ты можешь закрыть свои долги!", show_alert=True)
            return

        # получаем список долгов перед этим кредитором
        debts = await connection.fetch(
            """
            SELECT id, debt_sum
            FROM debts
            WHERE debtor_id = $1
              AND creditor_id = $2
              AND telegram_group_id = $3
              AND status = 'pending'
            """,
            callback_data.debtor_id,
            callback_data.creditor_id,
            callback_query.message.chat.id,
        )

        if not debts:
            await callback_query.message.edit_text("Нет долгов перед этим кредитором.")
            return

        # формируем список долгов
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"Долг {debt['debt_sum']} ⚣semen⚣",
                    callback_data=ReturnDebtAmountCallbackData(
                        debt_id=debt["id"],
                        debtor_id=callback_data.debtor_id
                    ).pack()
                )
            ]
            for debt in debts
        ]
        buttons.append([
            InlineKeyboardButton(text="Назад", callback_data=ReturnDebtNavigationCallbackData(action="back").pack())
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.edit_text("Выбери долг, который хочешь вернуть:", reply_markup=keyboard)

async def handle_return_debt_amount(callback_query: CallbackQuery, callback_data: ReturnDebtAmountCallbackData):
    pool = get_db_pool()

    async with pool.acquire() as connection:
        # проверяем, что запрос делает тот, кто должен вернуть долг
        current_user_id = await connection.fetchval(
            """
            SELECT id
            FROM users
            WHERE telegram_id = $1
              AND telegram_group_id = $2
            """,
            callback_query.from_user.id,
            callback_query.message.chat.id,
        )

        if current_user_id != callback_data.debtor_id:
            await callback_query.answer("Только ты можешь закрыть свои долги!", show_alert=True)
            return

        # получаем информацию о долге
        debt = await connection.fetchrow(
            """
            SELECT debt_sum, creditor_id
            FROM debts
            WHERE id = $1
              AND debtor_id = $2
              AND telegram_group_id = $3
              AND status = 'pending'
            """,
            callback_data.debt_id,
            callback_data.debtor_id,
            callback_query.message.chat.id,
        )

        if not debt:
            await callback_query.message.edit_text("Этот долг уже закрыт или не найден.")
            return

        debt_sum = debt["debt_sum"]
        creditor_id = debt["creditor_id"]

        # проверяем баланс должника
        debtor_balance = await connection.fetchval(
            """
            SELECT points
            FROM user_balance
            WHERE telegram_group_id = $1
              AND user_id = $2
            """,
            callback_query.message.chat.id,
            callback_data.debtor_id,
        )

        if debtor_balance < debt_sum:
            await callback_query.answer("У тебя недостаточно ⚣semen⚣ для закрытия этого долга!", show_alert=True)
            return

        # обновляем балансы и закрываем долг
        await connection.execute(
            """
            UPDATE user_balance
            SET points = points - $1
            WHERE telegram_group_id = $2
              AND user_id = $3
            """,
            debt_sum,
            callback_query.message.chat.id,
            callback_data.debtor_id,
        )

        await connection.execute(
            """
            UPDATE user_balance
            SET points = points + $1
            WHERE telegram_group_id = $2
              AND user_id = $3
            """,
            debt_sum,
            callback_query.message.chat.id,
            creditor_id,
        )

        await connection.execute(
            """
            UPDATE debts
            SET status = 'closed'
            WHERE id = $1
            """,
            callback_data.debt_id,
        )

    await callback_query.message.edit_text(f"Долг на сумму {debt_sum} мл. ⚣semen⚣ успешно закрыт!")

async def handle_return_debt_navigation(callback_query: CallbackQuery, callback_data: ReturnDebtNavigationCallbackData):
    if callback_data.action == "back":
        await callback_query.message.edit_text("Возврат долгов отменен.")