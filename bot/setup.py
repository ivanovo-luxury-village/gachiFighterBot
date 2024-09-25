from aiogram import Bot, Dispatcher
from utils.config import API_TOKEN

# инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()