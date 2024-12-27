import asyncio
from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db_pool import get_db_pool
from bot.setup import bot


### здесь будет функция дать в долг и попросить в долг : 
### функция попросить будет через кнопку  - потом меню 100 250 500 1000 
### выдача по кнопке    
# учесть что кнопки нажимает потом тот кто нажал выдать                          

### а еще функция вернуть долг с функцией выбора кому чере кнопку 

### понадобится витрина - долги : id date lender borrower telegram_group_id sum status (active, погашен)
### список должников /debts , через список 