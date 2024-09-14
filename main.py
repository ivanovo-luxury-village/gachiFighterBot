import logging
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand, FSInputFile, InputMediaAnimation, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.filters.callback_data import CallbackData
from datetime import datetime, timedelta
import random
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

# токен для бота
API_TOKEN = os.getenv('TOKEN')

# настройки подключения к базе данных
DB_HOST = os.getenv('POSTGRES_DB_HOST')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')
DB_PORT = os.getenv('POSTGRES_PORT')

# инициализация бота и диспетчера
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
pool = None

# класс для сallback событий выбора оружия
class WeaponCallbackData(CallbackData, prefix="choose_weapon"):
    weapon: str
    user_id: int
    duel_id: int

# функция для подключения к базе данных
async def create_db_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(user=DB_USER, password=DB_PASSWORD, database=DB_NAME, host=DB_HOST, port=DB_PORT)

# функция для отправки сообщений с задержкой
async def send_messages_with_delay(chat_id: int, messages: list, delay: float):
    for message in messages:
        await bot.send_message(chat_id, message)
        await asyncio.sleep(delay)

# регистрация нового пользователя
async def register_user(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id

    await create_db_pool()
    async with pool.acquire() as connection:
        existing_user = await connection.fetchval('SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2', chat_id, user_id)
        if existing_user:
            await message.reply('Ты уже зарегистрирован.')
        else:
            new_user_id = await connection.fetchval(
                'INSERT INTO users (telegram_group_id, telegram_id, username) VALUES ($1, $2, $3) RETURNING id', chat_id, user_id, username
            )
            await connection.execute('INSERT INTO user_balance (telegram_group_id, user_id, points) VALUES ($1, $2, 500)', chat_id, new_user_id)
            await message.reply('Ты успешно зарегистрирован!')

# выбор пидора дня
async def choose_pidor_of_the_day(message: types.Message):
    today = datetime.utcnow().date()
    chat_id = message.chat.id
    current_year = today.year

    await create_db_pool()
    async with pool.acquire() as connection:
        fighter_today = await connection.fetchrow('SELECT user_id FROM pidor_of_the_day WHERE telegram_group_id = $1 AND chosen_at = $2', chat_id, today)

        if fighter_today:
            user = await connection.fetchrow('SELECT username FROM users WHERE telegram_group_id = $1 AND id = $2', chat_id, fighter_today['user_id'])
            await message.reply(f'Согласно моей информации, по результатам сегодняшнего розыгрыша *пидор* дня: @{user["username"]}', parse_mode=ParseMode.MARKDOWN_V2)
        else:
            users = await connection.fetch('SELECT id, username FROM users WHERE telegram_group_id = $1', chat_id)
            if not users:
                await message.reply('Нет зарегистрированных пользователей.')
                return

            chosen_user = random.choice(users)
            await connection.execute('INSERT INTO pidor_of_the_day (user_id, chosen_at, chosen_year, telegram_group_id) VALUES ($1, $2, $3, $4)', chosen_user['id'], today, current_year, chat_id)
            await connection.execute('INSERT INTO statistics (user_id, chosen_count, chosen_year, telegram_group_id) VALUES ($1, 1, $2, $3) ON CONFLICT (user_id, chosen_year, telegram_group_id) DO UPDATE SET chosen_count = statistics.chosen_count + 1', chosen_user['id'], current_year, chat_id)

            scenario_id = await connection.fetchval('SELECT scenario_id FROM (SELECT DISTINCT scenario_id FROM messages WHERE message_type = $1) AS subquery ORDER BY random() LIMIT 1', 'INIT')
            messages = await connection.fetch('SELECT message_text FROM messages WHERE message_type = $1 AND scenario_id = $2 ORDER BY message_order', 'INIT', scenario_id)
            message_texts = [record['message_text'] for record in messages]
            await send_messages_with_delay(message.chat.id, message_texts, 2)

            # выбор случайного сообщения типа RESULT и вставка имени пользователя
            result_message_template = await connection.fetchval(
                'SELECT message_text FROM messages WHERE message_type = $1 ORDER BY random() LIMIT 1', 'RESULT'
            )
            result_message = result_message_template.replace('{username}', f'@{chosen_user["username"]}')
            await message.reply(result_message)

# функция отвечающая за дуэли
async def duel_command(message: types.Message):
    await create_db_pool()
    async with pool.acquire() as connection:
        try:
            chat_id = message.chat.id
            challenger_id = await connection.fetchval(
                'SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2', chat_id, message.from_user.id)
            logging.info(f'Challenger ID: {challenger_id}')
            
            if not challenger_id:
                await message.reply('Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться.')
                return

            challenged_id = None
            mentioned_username = None

            # сценарий 1: ответ на сообщение
            if message.reply_to_message:
                logging.info('Reply to message found.')
                challenged_id = await connection.fetchval(
                    'SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2', chat_id, message.reply_to_message.from_user.id)
                logging.info(f'Challenged ID from reply: {challenged_id}')

                if not challenged_id:
                    await message.reply('Пользователь, которому ты бросил вызов, не зарегистрирован в игре.')
                    logging.info('Challenged user is not registered.')
                    return

                # проверка, чтобы пользователь не мог вызвать сам себя на дуэль
                if challenger_id == challenged_id:
                    await message.reply('Ты не можешь вызвать на бой самого себя.')
                    return
                
                await message.reply(
                    f"@{message.reply_to_message.from_user.username}, *тебе бросили вызов*\! Поборешься с этим ♂jabroni♂\? \(/accept\)",
                    parse_mode=ParseMode.MARKDOWN_V2
                    )

            # сценарий 2: упоминание другого пользователя
            elif len(message.text.split()) > 1:
                mentioned_username = message.text.split()[1].strip('@')
                challenged_id = await connection.fetchval(
                    'SELECT id FROM users WHERE telegram_group_id = $1 AND username = $2', chat_id, mentioned_username)
                logging.info(f'Challenged ID from mention: {challenged_id}')

                if not challenged_id:
                    await message.reply(f'Пользователь @{mentioned_username} не зарегистрирован в игре.')
                    return

                # проверка, чтобы пользователь не мог вызвать сам себя на дуэль
                if challenger_id == challenged_id:
                    await message.reply('Ты не можешь вызвать на бой самого себя.')
                    return
            
                await message.reply(f"@{mentioned_username}, *тебе бросили вызов*\! Поборешься с этим ♂jabroni♂\? \(/accept\)",
                    parse_mode=ParseMode.MARKDOWN_V2
                    )
            
            # сценарий 3: открытая дуэль
            else:
                logging.info('Open duel created.')

                imgs_folder_path = './pics'
                all_imgs = [os.path.join(imgs_folder_path, file) for file in os.listdir(imgs_folder_path) if file.endswith('.jpg')]
                image_path = random.sample(all_imgs, 1)[0]

                image = FSInputFile(image_path)
                await bot.send_photo(
                    chat_id=chat_id, 
                    photo=image, 
                    caption='Я новый *♂dungeon master♂*\! Кто не согласен, отзовись или молчи вечно\! /accept\.', 
                    parse_mode='MarkdownV2'
                )

                result = await connection.execute(
                    'INSERT INTO duel_state (challenger_id, challenged_id, duel_type, telegram_group_id) VALUES ($1, $2, $3, $4)', 
                    challenger_id, None, 'open', chat_id
                )
                logging.info(f'Open Duel Insert Result: {result}')
                return

            # добавление дуэли в базу (кроме открытой дуэли)
            if challenged_id is not None:
                result = await connection.execute(
                    'INSERT INTO duel_state (challenger_id, challenged_id, duel_type, telegram_group_id) VALUES ($1, $2, $3, $4)', 
                    challenger_id, challenged_id, 'specific', chat_id
                )
                logging.info(f'Duel Insert Result: {result}')

        except Exception as e:
            logging.error(f'Error in duel_command: {e}')
            await message.reply('Произошла ошибка при создании дуэли. Попробуй еще раз.')

async def accept_duel_command(message: types.Message):
    await create_db_pool()
    async with pool.acquire() as connection:
        try:
            chat_id = message.chat.id
            user_id = await connection.fetchval(
                'SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2', 
                chat_id, message.from_user.id
            )

            if not user_id:
                await message.reply('Ты не зарегистрирован в игре. Используй команду /register, чтобы зарегистрироваться.')
                return
            
            current_time = datetime.utcnow()

            # сценарий 1 & 2: принятие вызова на конкретную дуэль (когда пользователь был вызван другим пользователем)
            logging.info('Searching for specific duel where user was challenged.')
            duel_info = await connection.fetchrow(
                'SELECT * FROM duel_state WHERE telegram_group_id = $1 AND challenged_id = $2 AND duel_type = $3 AND created_at > $4', 
                chat_id, user_id, 'specific', current_time - timedelta(minutes=5)
            )

            # если пользователь вызван на конкретную дуэль
            if duel_info:
                logging.info('Specific duel found, accepting...')

                # проверка: нельзя принять дуэль, созданную самим собой
                if duel_info['challenger_id'] == user_id:
                    await message.reply('Ты не можешь принять бой с самим собой.')
                    return

                # здесь мы не обновляем challenged_id, так как оно уже установлено в вызове дуэли
        
            # сценарий 3: принятие открытой дуэли
            else:
                logging.info('No specific duel found, searching for open duel.')
                duel_info = await connection.fetchrow(
                    'SELECT * FROM duel_state WHERE telegram_group_id = $1 AND challenged_id IS NULL AND created_at > $2 AND duel_type = $3',
                    chat_id, current_time - timedelta(minutes=5), 'open'
                )

                if not duel_info:
                    await message.reply('Нет доступных дуэлей для принятия.')
                    return
                
                # проверка: нельзя принять открытую дуэль от самого себя
                if duel_info['challenger_id'] == user_id:
                    await message.reply('Ты не можешь принять бой с самим собой.')
                    return

                # обновляем запись, добавляем challenged_id
                await connection.execute(
                    'UPDATE duel_state SET challenged_id = $1 WHERE telegram_group_id = $2 AND id = $3',
                    user_id, chat_id, duel_info['id']
                )

            # начинаем выбор оружия с вызвавшего на дуэль
            await choose_weapon(message, duel_info, duel_info['challenger_id'])

        except Exception as e:
            logging.error(f'Error in accept_duel_command: {e}')
            await message.reply('Произошла ошибка при принятии дуэли. Попробуйте еще раз.')

# функция для отправки кнопок с выбором оружия
async def choose_weapon(message: types.Message, duel_info, user_to_choose):
    duel_id = duel_info['id']
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="♂ Dick", callback_data=WeaponCallbackData(weapon="Dick", user_id=user_to_choose, duel_id=duel_id).pack()),
        InlineKeyboardButton(text="♂ Ass", callback_data=WeaponCallbackData(weapon="Ass", user_id=user_to_choose, duel_id=duel_id).pack()),
        InlineKeyboardButton(text="♂ Finger", callback_data=WeaponCallbackData(weapon="Finger", user_id=user_to_choose, duel_id=duel_id).pack())
    ]])

    # забираем username для пинга
    async with pool.acquire() as connection:
        username = await connection.fetchval(
            'SELECT username FROM users WHERE id = $1 AND telegram_group_id = $2', 
            user_to_choose, message.chat.id
        )

    # редактируем или отправляем сообщение для выбора
    if message.reply_markup:
        await message.edit_text(f"@{username}, выбери оружие:", reply_markup=keyboard)
    else:
        await message.answer(f"@{username}, выбери оружие:", reply_markup=keyboard)

# обработчик выбора оружия
async def weapon_chosen(callback_query: CallbackQuery, callback_data: WeaponCallbackData):
    telegram_user_id = callback_query.from_user.id
    weapon = callback_data.weapon
    duel_id = callback_data.duel_id
    message = callback_query.message
    chat_id = message.chat.id

    # получаем информацию о дуэли по конкретному duel_id
    async with pool.acquire() as connection:
        duel_info = await connection.fetchrow(
            'SELECT * FROM duel_state WHERE id = $1 AND telegram_group_id = $2', 
            duel_id, chat_id
        )

        if not duel_info:
            await callback_query.answer("Дуэль не найдена")
            return

        # получаем внутренний id пользователя по его telegram_id
        user_id = await connection.fetchval(
            'SELECT id FROM users WHERE telegram_id = $1 AND telegram_group_id = $2', 
            telegram_user_id, chat_id
        )

        if not user_id:
            await callback_query.answer("Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться.")
            return

        # проверяем, кто сейчас должен выбирать оружие
        if duel_info['challenger_weapon'] is None and user_id == duel_info['challenger_id']:
            # если вызвавший на дуэль выбирает оружие
            await connection.execute(
                'UPDATE duel_state SET challenger_weapon = $1 WHERE id = $2',
                weapon, duel_info['id']
            )
            await callback_query.answer(f"Ты выбрал {weapon}")
            await choose_weapon(message, duel_info, duel_info['challenged_id'])

        elif duel_info['challenger_weapon'] is not None and user_id == duel_info['challenged_id']:
            # если вызванный на дуэль выбирает оружие
            await connection.execute(
                'UPDATE duel_state SET challenged_weapon = $1 WHERE id = $2',
                weapon, duel_info['id']
            )
            await callback_query.answer(f"Ты выбрал {weapon}")
            await callback_query.message.edit_reply_markup(reply_markup=None)

            # начинаем дуэль после выбора оружия
            await start_duel(message, duel_info, user_id, chat_id)
        
        else:
            # если это не их очередь выбирать
            await callback_query.answer("Сейчас не твоя очередь выбирать оружие.", show_alert=True)

async def start_duel(message: types.Message, duel_info, user_id, chat_id):
    await create_db_pool()
    async with pool.acquire() as connection:    
        try:
            await message.reply('Борьба началась!')

            # отправка GIF-изображений
            gif_folder_path = './gifs'
            all_gifs = [os.path.join(gif_folder_path, file) for file in os.listdir(gif_folder_path) if file.endswith('.gif')]
            gif_files = random.sample(all_gifs, 3)

            first_gif = FSInputFile(gif_files[0])
            sent_message = await bot.send_animation(message.chat.id, first_gif)

            # задержка и смена GIF-изображений
            for gif in gif_files[1:]:
                await asyncio.sleep(2)
                new_gif = FSInputFile(gif)
                media = InputMediaAnimation(media=new_gif)  # передача объекта файла как параметра media
                await bot.edit_message_media(media=media, chat_id=message.chat.id, message_id=sent_message.message_id)

            # удаление сообщения с GIF-картинкой
            await asyncio.sleep(3)  # задержка перед удалением
            await bot.delete_message(chat_id=message.chat.id, message_id=sent_message.message_id)

            # рандомный выбор победителя и обновление баланса
            winner_id = random.choice([duel_info['challenger_id'], user_id])
            loser_id = duel_info['challenger_id'] if winner_id != duel_info['challenger_id'] else user_id
            points = int(random.expovariate(1/50))

            await connection.execute('UPDATE user_balance SET points = points + $1 WHERE telegram_group_id = $2 AND user_id = $3', points, chat_id, winner_id)
            await connection.execute('UPDATE user_balance SET points = points - $1 WHERE telegram_group_id = $2 AND user_id = $3', points, chat_id, loser_id)
            await connection.execute('INSERT INTO fight_history (winner_id, loser_id, points_won, points_lost, telegram_group_id) VALUES ($1, $2, $3, $3, $4)', winner_id, loser_id, points, chat_id)
            await connection.execute('DELETE FROM duel_state WHERE telegram_group_id = $1 AND id = $2', chat_id, duel_info['id'])

            winner_name = await connection.fetchval('SELECT username FROM users WHERE telegram_group_id = $1 AND id = $2', chat_id, winner_id)
            await message.reply(f'Победитель дуэли: @{winner_name}. Выиграно {points} ♂️semen!')

        except Exception as e:
            logging.error(f'Error in start_duel: {e}')
            await message.reply('Произошла ошибка в ходе дуэли. Попробуйте еще раз.')

# вывод статистики
async def rating(message: types.Message):
    await create_db_pool()
    current_year = datetime.utcnow().year
    chat_id = message.chat.id

    async with pool.acquire() as connection:
        stats = await connection.fetch(
            '''
            SELECT 
                users.username
                , COALESCE(statistics.chosen_count, 0) AS chosen_count
            FROM users
            LEFT JOIN statistics 
                ON users.id = statistics.user_id 
                    AND users.telegram_group_id = statistics.telegram_group_id
                    AND statistics.chosen_year = $1
            WHERE 1=1
                AND users.telegram_group_id = $2
            ORDER BY chosen_count DESC
            ''', current_year, chat_id 
        )

        if not stats:
            await message.reply('Статистика пока пуста.')
        else:
            stats_message = f"Рейтинг пидоров (данные актуальны на {current_year} год):\n"
            for idx, stat in enumerate(stats, start=1):
                stats_message += f"{idx}. {stat['username']}: {stat['chosen_count']} раз\n"
            await message.reply(stats_message)

async def show_fight_stats(message: types.Message):
    await create_db_pool()

    chat_id = message.chat.id
    
    async with pool.acquire() as connection:
        stats = await connection.fetch(
            '''
            SELECT 
                users.username
                , COUNT(CASE WHEN fight_history.winner_id = users.id THEN 1 END) AS wins
                , COUNT(CASE WHEN fight_history.loser_id = users.id THEN 1 END) AS losses
                , COALESCE(user_balance.points, 0) AS current_balance
            FROM users
            LEFT JOIN fight_history 
                ON (users.id = fight_history.winner_id OR users.id = fight_history.loser_id)
                    AND users.telegram_group_id = fight_history.telegram_group_id
            LEFT JOIN user_balance 
                ON users.id = user_balance.user_id
                    AND users.telegram_group_id = user_balance.telegram_group_id
            WHERE 1=1
                AND users.telegram_group_id = $1
            GROUP BY users.username, user_balance.points
            ORDER BY current_balance DESC
            ''', chat_id
        )

        if not stats:
            await message.reply('Статистика поединков пока пуста.')
        else:
            stats_message = "Статистика по боям:\n"
            for idx, stat in enumerate(stats, start=1):
                stats_message += (f"{idx}. {stat['username']}: Победы: {stat['wins']}, "
                                  f"Поражения: {stat['losses']}, "
                                  f"Количество ♂️semen♂️: {stat['current_balance']}\n")
            await message.reply(stats_message)

async def main():
    await bot.set_my_commands([
        BotCommand(command="pidor", description="Выбрать пидора дня"),
        BotCommand(command="register", description="Зарегистрироваться"),
        BotCommand(command="rating", description="Рейтинг пидорасов"),
        BotCommand(command="duel", description="Вызвать побороться"),
        BotCommand(command="accept", description="Принять бой"),
        BotCommand(command="fight_stats", description="Статистика боев")
    ])

    dp.message.register(register_user, Command(commands=["register"]))
    dp.message.register(choose_pidor_of_the_day, Command(commands=["pidor"]))
    dp.message.register(rating, Command(commands=["rating"]))
    dp.message.register(duel_command, Command(commands=["duel"]))
    dp.message.register(accept_duel_command, Command(commands=["accept"]))
    dp.message.register(show_fight_stats, Command(commands=["fight_stats"]))
    dp.callback_query.register(weapon_chosen, WeaponCallbackData.filter())

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())