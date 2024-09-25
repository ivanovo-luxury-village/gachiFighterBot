import os
from dotenv import load_dotenv

load_dotenv()

# токен для бота
API_TOKEN = os.getenv("TOKEN")
APP_HOST = os.getenv("APP_HOST")
APP_PORT = os.getenv("APP_PORT")

WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"