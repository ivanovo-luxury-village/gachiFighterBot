import random
from aiogram import types
from datetime import datetime
from database.db_pool import get_db_pool
from bot.setup import bot

async def slap_command(message: types.Message):
    pool = get_db_pool()
    chat_id = message.chat.id
    today = datetime.utcnow().date()
    
    # проверка наличия упоминания пользователя через @
    if not message.entities or not any(entity.type == "mention" for entity in message.entities):
        await message.reply("Упомяни через @!")
        return
    
    # получение имени упомянутого пользователя из текста сообщения
    mentioned_entity = next((entity for entity in message.entities if entity.type == "mention"), None)
    if not mentioned_entity:
        await message.reply("Неправильное упоминание пользователя!")
        return
    
    # получаем имя без символа @
    mentioned_username = message.text[mentioned_entity.offset + 1:mentioned_entity.offset + mentioned_entity.length]  

    async with pool.acquire() as connection:
        target_user = await connection.fetchrow(
            "SELECT id FROM users WHERE telegram_group_id = $1 AND username = $2",
            chat_id,
            mentioned_username,
        )
        
        if not target_user:
            await message.reply("Пользователь не зарегистрирован!")
            return
        
        target_user_id = target_user['id']
        slapper_telegram_id = message.from_user.id
        slapper_user = await connection.fetchrow(
            "SELECT id FROM users WHERE telegram_group_id = $1 AND telegram_id = $2",
            chat_id,
            slapper_telegram_id,
        )
        
        if not slapper_user:
            await message.reply("Ты не зарегистрирован. Используй команду /register, чтобы зарегистрироваться.")
            return
        
        slapper_user_id = slapper_user['id']
        pidor_today = await connection.fetchrow(
            "SELECT user_id FROM pidor_of_the_day WHERE telegram_group_id = $1 AND chosen_at = $2",
            chat_id,
            today,
        )
        
        if not pidor_today:
            await message.reply("<b>Пидор</b> дня еще не выбран!", parse_mode='HTML')
            return

        if pidor_today['user_id'] != slapper_user_id:
            await message.reply("Только <b>пидор</b> дня может выполнить удар!", parse_mode='HTML')
            return
        
        last_slap_time = await connection.fetchval(
            "SELECT slap_time FROM slaps WHERE telegram_group_id = $1 AND slapper_user_id = $2 ORDER BY slap_time DESC LIMIT 1",
            chat_id,
            slapper_user_id,
        )
        
        if last_slap_time and last_slap_time.date() == today:
            await message.reply("Ты можешь ударить только раз в день!")
            return

        points = random.randint(10,70)
        current_balance = await connection.fetchval(
            "SELECT points FROM user_balance WHERE telegram_group_id = $1 AND user_id = $2",
            chat_id, target_user_id
        )
        points_to_deduct = min(points, current_balance)
        
        await connection.execute(
            "UPDATE user_balance SET points = points - $1 WHERE telegram_group_id = $2 AND user_id = $3",
            points_to_deduct,
            chat_id,
            target_user_id,
        )
        
        await connection.execute(
            """
            INSERT INTO slaps (telegram_group_id, slapper_user_id, target_user_id, points_deducted, slap_time) 
            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            """,
            chat_id,
            slapper_user_id,
            target_user_id,
            points_to_deduct,
        )

    message_text = f"""
⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠛⢉⢉⠉⠉⠻⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⠟⠠⡰⣕⣗⣷⣧⣀⣅⠘⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⠃⣠⣳⣟⣿⣿⣷⣿⡿⣜⠄⣿⣿⣿⣿⣿
⣿⣿⣿⣿⡿⠁⠄⣳⢷⣿⣿⣿⣿⡿⣝⠖⠄⣿⣿⣿⣿⣿
⣿⣿⣿⣿⠃⠄⢢⡹⣿⢷⣯⢿⢷⡫⣗⠍⢰⣿⣿⣿⣿⣿
⣿⣿⣿⡏⢀⢄⠤⣁⠋⠿⣗⣟⡯⡏⢎⠁⢸⣿⣿⣿⣿⣿
⣿⣿⣿⠄⢔⢕⣯⣿⣿⡲⡤⡄⡤⠄⡀⢠⣿⣿⣿⣿⣿⣿
⣿⣿⠇⠠⡳⣯⣿⣿⣾⢵⣫⢎⢎⠆⢀⣿⣿⣿⣿⣿⣿⣿
⣿⣿⠄⢨⣫⣿⣿⡿⣿⣻⢎⡗⡕⡅⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⠄⢜⢾⣾⣿⣿⣟⣗⢯⡪⡳⡀⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⠄⢸⢽⣿⣷⣿⣻⡮⡧⡳⡱⡁⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⡄⢨⣻⣽⣿⣟⣿⣞⣗⡽⡸⡐⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⡇⢀⢗⣿⣿⣿⣿⡿⣞⡵⡣⣊⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⡀⡣⣗⣿⣿⣿⣿⣯⡯⡺⣼⠎⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣧⠐⡵⣻⣟⣯⣿⣷⣟⣝⢞⡿⢹⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⡆⢘⡺⣽⢿⣻⣿⣗⡷⣹⢩⢃⢿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣷⠄⠪⣯⣟⣿⢯⣿⣻⣜⢎⢆⠜⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⡆⠄⢣⣻⣽⣿⣿⣟⣾⡮⡺⡸⠸⣿⣿⣿⣿
⣿⣿⡿⠛⠉⠁⠄⢕⡳⣽⡾⣿⢽⣯⡿⣮⢚⣅⠹⣿⣿⣿
⡿⠋⠄⠄⠄⠄⢀⠒⠝⣞⢿⡿⣿⣽⢿⡽⣧⣳⡅⠌⠻⣿
⠁⠄⠄⠄⠄⠄⠐⡐⠱⡱⣻⡻⣝⣮⣟⣿⣻⣟⣻⡺⣊
@{message.from_user.username} <b>ударил</b> своим ♂Dick♂ @{mentioned_username} и отнял {points_to_deduct} ⚣semen⚣!
Такого в ⚣gym⚣ обычно не прощают!
"""
    await bot.send_message(chat_id, message_text, parse_mode='HTML')
