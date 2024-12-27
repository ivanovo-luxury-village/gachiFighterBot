import asyncio
import uvicorn

from database.db_pool import create_db_pool, get_db_pool

from aiogram.types import BotCommand
from aiogram.filters import Command
from fastapi import FastAPI
from fastapi.requests import Request
from contextlib import asynccontextmanager
from contextlib import asynccontextmanager

from bot.setup import bot, dp
from bot.register import register_user
from bot.pidor_daily import choose_pidor_of_the_day
from bot.create_duel import duel_command, DuelCallbackData
from bot.accept_duel import callback_accept_duel
from bot.weapons import WeaponCallbackData, weapon_chosen
from bot.stats import show_fight_stats, show_global_fight_stats, rating
from bot.slap import slap_command
from bot.release_notes import release
from bot.debts import (
    request_debt, 
    handle_debt_request, 
    handle_debt_amount, 
    handle_cancel_debt_request, 
    DebtRequestCallbackData, 
    DebtAmountCallbackData
    )
#from bot.suck import *

from utils.config import APP_HOST, APP_PORT, WEBHOOK_SECRET, WEBHOOK_URL
from utils.logger import logger
from utils.checks import check_expired_duels, check_long_in_progress_duels


commands = [
    BotCommand(command="register", description="Зарегистрироваться"),
    BotCommand(command="pidor", description="Выбрать пидора дня"),
    BotCommand(command="rating", description="Рейтинг пидоров"),
    BotCommand(command="fight", description="Вызвать побороться"),
    BotCommand(command="hit", description="Ударить членом по лбу"),
    BotCommand(command="fight_stats", description="Статистика боев"),
    BotCommand(command="global_fight_stats", description="Глобальная статистика боев"),
    BotCommand(command="get_semen", description="Взять в долг semen"),
    #BotCommand(command="return_semen", description="Вернуть долг"),
    #BotCommand(command="suck_me", description="Предложить минет"),
]


async def set_commands():
    await bot.set_my_commands(commands)

    dp.message.register(register_user, Command(commands=["register"]))
    dp.message.register(choose_pidor_of_the_day, Command(commands=["pidor"]))
    dp.message.register(rating, Command(commands=["rating"]))
    dp.message.register(duel_command, Command(commands=["fight"]))
    dp.message.register(slap_command, Command(commands=["hit"]))
    dp.message.register(show_fight_stats, Command(commands=["fight_stats"]))
    dp.message.register(show_global_fight_stats, Command(commands=["global_fight_stats"]))
    dp.message.register(release, Command(commands=["release"]))
    dp.message.register(request_debt, Command(commands=["get_semen"]))
    #dp.message.register(_________, Command(commands=["return_semen"]))
    #dp.message.register(_________, Command(commands=["suck_me"]))
    dp.callback_query.register(callback_accept_duel, DuelCallbackData.filter())
    dp.callback_query.register(weapon_chosen, WeaponCallbackData.filter())
    dp.callback_query.register(handle_debt_request, DebtRequestCallbackData.filter())
    dp.callback_query.register(handle_debt_amount, DebtAmountCallbackData.filter())
    dp.callback_query.register(handle_cancel_debt_request, lambda cb: cb.data == "cancel_debt_request")


async def start_background_tasks():
    logger.info("Starting background tasks after initialization delay...")
    await asyncio.sleep(1)  # Задержка в 1 секунду перед запуском задач

    pool = get_db_pool()
    
    if pool is None:
        logger.error("Database pool is not initialized before starting tasks.")
    else:
        logger.info("Database pool is correctly initialized before starting tasks.")
    
    asyncio.create_task(check_expired_duels())
    asyncio.create_task(check_long_in_progress_duels())


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting lifespan and initializing database pool...")
    await create_db_pool()

    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    await set_commands()

    # запуск проверок дуэлей
    await start_background_tasks()

    webhook_info = await bot.get_webhook_info()
    logger.info(f"Webhook url: {webhook_info.url}")
    yield
    logger.info("Lifecycle shutdown successful!")


app = FastAPI(lifespan=lifespan, title="API")


@app.get("/healthz")
def get_health() -> str:
    return "up and running!"


@app.post("/webhook")
async def webhook(request: Request) -> None:
    await dp.feed_webhook_update(bot, await request.json())


if __name__ == "__main__":
    logger.info("API is starting up")
    uvicorn.run(
        app,
        host=APP_HOST,
        port=int(APP_PORT),
        log_config="./log_conf.yaml",
        timeout_graceful_shutdown=30,
    )