from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db_pool import get_db_pool


class DebtRequestCallbackData(CallbackData, prefix="debt_request"):
    action: str
    user_id: int

class DebtAmountCallbackData(CallbackData, prefix="debt_amount"):
    amount: int
    creditor_id: int
    debtor_id: int

async def request_debt(message: types.Message):
    debtor_id = message.from_user.id

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

    await message.answer("У меня нет очков. Дайте мне очки в долг!", reply_markup=buttons)

async def handle_debt_request(callback_query: CallbackQuery, callback_data: DebtRequestCallbackData):
    creditor_id = callback_query.from_user.id
    debtor_id = callback_data.user_id

    if creditor_id == debtor_id:
        await callback_query.answer("Ты не можешь дать долг самому себе!", show_alert=True)
        return

    # проверяем, что запрос идет только от нажавшего кнопку
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="100 очков", callback_data=DebtAmountCallbackData(amount=100, creditor_id=creditor_id, debtor_id=debtor_id).pack())],
            [InlineKeyboardButton(text="250 очков", callback_data=DebtAmountCallbackData(amount=250, creditor_id=creditor_id, debtor_id=debtor_id).pack())],
            [InlineKeyboardButton(text="500 очков", callback_data=DebtAmountCallbackData(amount=500, creditor_id=creditor_id, debtor_id=debtor_id).pack())],
            [InlineKeyboardButton(text="1000 очков", callback_data=DebtAmountCallbackData(amount=1000, creditor_id=creditor_id, debtor_id=debtor_id).pack())],
        ]
    )

    await callback_query.message.edit_text("Выберите сумму долга:", reply_markup=buttons)

async def handle_debt_amount(callback_query: CallbackQuery, callback_data: DebtAmountCallbackData):
    creditor_id = callback_data.creditor_id
    debtor_id = callback_data.debtor_id
    amount = callback_data.amount

    if callback_query.from_user.id != creditor_id:
        await callback_query.answer("Эту кнопку может нажимать только кредитор!", show_alert=True)
        return

    pool = get_db_pool()
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

    await callback_query.message.edit_text(f"Долг на сумму {amount} очков успешно создан!")
    await callback_query.answer("Долг создан!")