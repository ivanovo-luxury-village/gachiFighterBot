import logging
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, InputFile, FSInputFile, InputMediaAnimation
from aiogram.filters import Command
from datetime import datetime, timedelta
import random
import asyncio
import creds

# токен для бота
API_TOKEN = creds.TOKEN

# настройки подключения к базе данных
DB_HOST = creds.DB_HOST
DB_USER = creds.DB_USER
DB_PASSWORD = creds.DB_PASSWORD
DB_NAME = creds.DB_NAME
DB_PORT = creds.DB_PORT

# инициализация бота и диспетчера
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
pool = None

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

    await create_db_pool()
    async with pool.acquire() as connection:
        existing_user = await connection.fetchval('SELECT id FROM users WHERE telegram_id = $1', user_id)
        if existing_user:
            await message.reply('Вы уже зарегистрированы.')
        else:
            new_user_id = await connection.fetchval(
                'INSERT INTO users (telegram_id, username) VALUES ($1, $2) RETURNING id', user_id, username
            )
            await connection.execute('INSERT INTO user_balance (user_id, points) VALUES ($1, 500)', new_user_id)
            await message.reply('Вы успешно зарегистрированы!')

# выбор пидора дня
async def choose_pidor_of_the_day(message: types.Message):
    today = datetime.utcnow().date()
    current_year = today.year

    await create_db_pool()
    async with pool.acquire() as connection:
        fighter_today = await connection.fetchrow('SELECT user_id FROM pidor_of_the_day WHERE chosen_at = $1', today)

        if fighter_today:
            user = await connection.fetchrow('SELECT username FROM users WHERE id = $1', fighter_today['user_id'])
            await message.reply(f'Пидор дня: @{user["username"]}')
        else:
            users = await connection.fetch('SELECT id, username FROM users')
            if not users:
                await message.reply('Нет зарегистрированных пользователей.')
                return

            chosen_user = random.choice(users)
            await connection.execute('INSERT INTO pidor_of_the_day (user_id, chosen_at, chosen_year) VALUES ($1, $2, $3)', chosen_user['id'], today, current_year)
            await connection.execute('INSERT INTO statistics (user_id, chosen_count, chosen_year) VALUES ($1, 1, $2) ON CONFLICT (user_id, chosen_year) DO UPDATE SET chosen_count = statistics.chosen_count + 1', chosen_user['id'], current_year)

            scenario_id = await connection.fetchval('SELECT scenario_id FROM (SELECT DISTINCT scenario_id FROM messages WHERE message_type = $1) AS subquery ORDER BY random() LIMIT 1', 'INIT')
            messages = await connection.fetch('SELECT message_text FROM messages WHERE message_type = $1 AND scenario_id = $2 ORDER BY message_order', 'INIT', scenario_id)
            message_texts = [record['message_text'] for record in messages]
            await send_messages_with_delay(message.chat.id, message_texts, 1.5)

            await message.reply(f"Итак, пидор дня @{chosen_user['username']}!")

# функция отвечающая за дуэли
async def duel_command(message: types.Message):
    await create_db_pool()
    async with pool.acquire() as connection:
        try:
            # проверка, зарегистрирован ли пользователь, вызвавший команду
            challenger_id = await connection.fetchval(
                'SELECT id FROM users WHERE telegram_id = $1', message.from_user.id)
            logging.info(f'Challenger ID: {challenger_id}')
            
            if not challenger_id:
                await message.reply('Вы не зарегистрированы. Пожалуйста, используйте команду /register, чтобы зарегистрироваться.')
                return

            challenged_id = None
            mentioned_username = None
            
            # проверка, если команда содержит упоминание другого пользователя
            if len(message.text.split()) > 1:
                mentioned_username = message.text.split()[1].strip('@')
                challenged_id = await connection.fetchval(
                    'SELECT id FROM users WHERE username = $1', mentioned_username)
                logging.info(f'Challenged ID from mention: {challenged_id}')

                if not challenged_id:
                    await message.reply(f'Пользователь @{mentioned_username} не зарегистрирован в игре.')
                    return

            # проверка на наличие ответного сообщения
            elif message.reply_to_message:
                logging.info('Reply to message found.')
                challenged_id = await connection.fetchval(
                    'SELECT id FROM users WHERE telegram_id = $1', message.reply_to_message.from_user.id)
                logging.info(f'Challenged ID from reply: {challenged_id}')

                if not challenged_id:
                    await message.reply('Пользователь, которому вы бросили вызов, не зарегистрирован в игре.')
                    logging.info('Challenged user is not registered.')
                    return
            
            else:
                await message.reply('Чтобы вызвать кого-то на бой, вы должны упомянуть его @username или ответить на сообщение этого пользователя.')
                logging.info('No mention or reply to message found.')
                return
            
            # проверка, чтобы пользователь не мог вызвать сам себя на дуэль
            if challenger_id == challenged_id:
                await message.reply('Вы не можете вызвать на бой самого себя.')
                return

            if mentioned_username:
                await message.reply(f'@{mentioned_username}, вас вызвали побороться! Примете вызов? (/accept)')
            else:
                await message.reply(f'@{message.reply_to_message.from_user.username}, вас вызвали на бой! Примете вызов? (/accept)')

            # Логика для отслеживания состояния дуэли
            result = await connection.execute(
                'INSERT INTO duel_state (challenger_id, challenged_id) VALUES ($1, $2)', 
                challenger_id, challenged_id
            )
            
            logging.info(f'Duel Insert Result: {result}')
            if result == 'INSERT 0 1':
                logging.info(f'Duel created: Challenger {challenger_id}, Challenged {challenged_id}')
            else:
                logging.error(f'Failed to insert duel: Challenger {challenger_id}, Challenged {challenged_id}, Result: {result}')

        except Exception as e:
            logging.error(f'Error in duel_command: {e}')
            await message.reply('Произошла ошибка при создании дуэли. Попробуйте еще раз.')

async def accept_duel_command(message: types.Message):
    await create_db_pool()
    async with pool.acquire() as connection:
        try:
            # получаем внутренний ID пользователя из таблицы users
            user_id = await connection.fetchval(
                'SELECT id FROM users WHERE telegram_id = $1', 
                message.from_user.id
            )

            # если пользователь не найден, отправляем сообщение и выходим
            if not user_id:
                await message.reply('Вы не зарегистрированы в игре. Пожалуйста, используйте команду /register, чтобы зарегистрироваться.')
                return
            
            # получаем текущее время в UTC
            current_time = datetime.utcnow()

            # логирование текущего времени и всех дуэлей в таблице
            all_duels = await connection.fetch(
                'SELECT * FROM duel_state WHERE challenged_id = $1', user_id
            )

            if not all_duels:
                await message.reply('У вас нет активных боев для принятия.')
                return

            # выбор дуэлей с учетом временной зоны
            duel_info = await connection.fetchrow(
                'SELECT * FROM duel_state WHERE challenged_id = $1 AND created_at > $2',
                user_id, current_time - timedelta(minutes=5)
            )

            if not duel_info:
                await message.reply('Нет активных боев для принятия.')
                return

            await message.reply('Борьба началась!')

            # отправка первой GIF-изображения
            gif_files = [
                'gifs/gif4.gif', 
                'gifs/optimized_gif2.gif', 
                'gifs/optimized_gif1.gif'
            ]
            first_gif = FSInputFile(gif_files[0])
            sent_message = await bot.send_animation(message.chat.id, first_gif)

            # задержка и смена GIF-изображений
            for gif in gif_files[1:]:
                await asyncio.sleep(2)
                new_gif = FSInputFile(gif)
                media = InputMediaAnimation(media=new_gif)  # передача объекта файла как параметра media
                await bot.edit_message_media(media=media, chat_id=message.chat.id, message_id=sent_message.message_id)

            # удаление сообщения с GIF-картинкой
            await asyncio.sleep(2)  # задержка перед удалением
            await bot.delete_message(chat_id=message.chat.id, message_id=sent_message.message_id)

            # рандомный выбор победителя и обновление баланса
            winner_id = random.choice([duel_info['challenger_id'], duel_info['challenged_id']])
            loser_id = duel_info['challenger_id'] if winner_id != duel_info['challenger_id'] else duel_info['challenged_id']
            points = int(random.expovariate(1/50))

            await connection.execute('UPDATE user_balance SET points = points + $1 WHERE user_id = $2', points, winner_id)
            await connection.execute('UPDATE user_balance SET points = points - $1 WHERE user_id = $2', points, loser_id)
            await connection.execute('INSERT INTO fight_history (winner_id, loser_id, points_won, points_lost) VALUES ($1, $2, $3, $3)', winner_id, loser_id, points)
            await connection.execute('DELETE FROM duel_state WHERE challenger_id = $1 AND challenged_id = $2', duel_info['challenger_id'], duel_info['challenged_id'])

            winner_name = await connection.fetchval('SELECT username FROM users WHERE id = $1', winner_id)
            await message.reply(f'Победитель дуэли: @{winner_name}. Выиграно {points} ♂️semen!')

        except Exception as e:
            logging.error(f'Error in accept_duel_command: {e}')
            await message.reply('Произошла ошибка при принятии дуэли. Попробуйте еще раз.')

# вывод статистики
async def rating(message: types.Message):
    await create_db_pool()
    current_year = datetime.utcnow().year

    async with pool.acquire() as connection:
        stats = await connection.fetch(
            '''
            SELECT 
                users.username
                , COALESCE(statistics.chosen_count, 0) AS chosen_count
            FROM users
            LEFT JOIN statistics 
                ON users.id = statistics.user_id AND statistics.chosen_year = $1
            ORDER BY chosen_count DESC
            ''', current_year
        )

        if not stats:
            await message.reply('Статистика пока пуста.')
        else:
            stats_message = f"Рейтинг пидоров (данные актуальны на {current_year} год):\n" + \
                            "\n".join([f"@{stat['username']}: {stat['chosen_count']} раз" for stat in stats])
            await message.reply(stats_message)

async def show_fight_stats(message: types.Message):
    await create_db_pool()
    
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
                ON users.id = fight_history.winner_id 
                    OR users.id = fight_history.loser_id
            LEFT JOIN user_balance 
                ON users.id = user_balance.user_id
            GROUP BY users.username, user_balance.points
            ORDER BY current_balance DESC
            '''
        )

        if not stats:
            await message.reply('Статистика боев пока пуста.')
        else:
            stats_message = "Статистика по боям:\n"
            for stat in stats:
                stats_message += (f"@{stat['username']}: Победы: {stat['wins']}, "
                                  f"Поражения: {stat['losses']}, "
                                  f"Количество ♂️semen: {stat['current_balance']}\n")
            await message.reply(stats_message)

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Выбрать пидора дня"),
        BotCommand(command="register", description="Зарегистрироваться"),
        BotCommand(command="rating", description="Рейтинг пидорасов"),
        BotCommand(command="duel", description="Вызвать побороться"),
        BotCommand(command="accept", description="Принять бой"),
        BotCommand(command="fight_stats", description="Статистика боев")
    ])

    dp.message.register(register_user, Command(commands=["register"]))
    dp.message.register(choose_pidor_of_the_day, Command(commands=["start"]))
    dp.message.register(rating, Command(commands=["rating"]))
    dp.message.register(duel_command, Command(commands=["duel"]))
    dp.message.register(accept_duel_command, Command(commands=["accept"]))
    dp.message.register(show_fight_stats, Command(commands=["fight_stats"]))

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())