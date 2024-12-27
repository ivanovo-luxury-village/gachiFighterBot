import os
import random
import asyncio
from aiogram import types
from aiogram.types import FSInputFile, InputMediaAnimation
from database.db_pool import get_db_pool
from utils.service_funcs import SafeDict
from utils.distribute_points import approx_points
from utils.logger import logger
from bot.setup import bot


async def start_duel(message: types.Message, duel_info, chat_id, winner):
    pool = get_db_pool()
    async with pool.acquire() as connection:
        try:
            # отправка GIF-изображений
            gif_folder_path = "./media/gifs/duel_progress"
            all_gifs = [
                os.path.join(gif_folder_path, file)
                for file in os.listdir(gif_folder_path)
                if file.endswith(".gif")
            ]
            gif_files = random.sample(all_gifs, 3)

            first_gif = FSInputFile(gif_files[0])
            sent_message = await bot.send_animation(message.chat.id, first_gif)

            # задержка и смена GIF-изображений
            for gif in gif_files[1:]:
                await asyncio.sleep(2)
                new_gif = FSInputFile(gif)
                media = InputMediaAnimation(
                    media=new_gif
                )  # передача объекта файла как параметра media
                await bot.edit_message_media(
                    media=media,
                    chat_id=message.chat.id,
                    message_id=sent_message.message_id,
                )

            # удаление сообщения с GIF-картинкой
            await asyncio.sleep(3)  # задержка перед удалением
            await bot.delete_message(
                chat_id=message.chat.id, message_id=sent_message.message_id
            )

            # выбор победителя исходя из выбранного оружия и обновление баланса
            if winner == "challenger":
                winner_id = duel_info["challenger_id"]
                loser_id = duel_info["challenged_id"]
            else:
                winner_id = duel_info["challenged_id"]
                loser_id = duel_info["challenger_id"]

            points = approx_points()
            
            await connection.execute(
                "UPDATE user_balance SET points = points + $1 WHERE telegram_group_id = $2 AND user_id = $3",
                points,
                chat_id,
                winner_id,
            )
            await connection.execute(
                "UPDATE user_balance SET points = points - $1 WHERE telegram_group_id = $2 AND user_id = $3",
                points,
                chat_id,
                loser_id,
            )

            # получаем обновленные балансы пользователей
            winner_balance_after = await connection.fetchval(
                "SELECT points FROM user_balance WHERE telegram_group_id = $1 AND user_id = $2",
                chat_id,
                winner_id,
            )
            loser_balance_after = await connection.fetchval(
                "SELECT points FROM user_balance WHERE telegram_group_id = $1 AND user_id = $2",
                chat_id,
                loser_id,
            )

            # получаем оружие напрямую из базы данных (duel_state)
            weapons_state = await connection.fetchrow(
                "SELECT challenger_weapon, challenged_weapon FROM duel_state WHERE id = $1 AND telegram_group_id = $2",
                duel_info["id"],
                chat_id,
            )

            # получаем имена пользователей для вывода и выбранное оружие
            winner_name = await connection.fetchval(
                "SELECT username FROM users WHERE telegram_group_id = $1 AND id = $2",
                chat_id,
                winner_id,
            )
            loser_name = await connection.fetchval(
                "SELECT username FROM users WHERE telegram_group_id = $1 AND id = $2",
                chat_id,
                loser_id,
            )

            winner_weapon = (
                weapons_state["challenger_weapon"]
                if winner_id == duel_info["challenger_id"]
                else weapons_state["challenged_weapon"]
            )
            loser_weapon = (
                weapons_state["challenged_weapon"]
                if loser_id == duel_info["challenged_id"]
                else weapons_state["challenger_weapon"]
            )

            # сообщение о результате поединка в зависимости от очков
            if points < 30:
                fight_result_message_template = await connection.fetchval(
                    "SELECT message_text FROM messages WHERE message_type = 'FIGHT_RESULT_WEAK' ORDER BY random() LIMIT 1"
                )
            elif points >= 30 and points < 250:
                fight_result_message_template = await connection.fetchval(
                    "SELECT message_text FROM messages WHERE message_type = 'FIGHT_RESULT' ORDER BY random() LIMIT 1"
                )
            else:
                fight_result_message_template = await connection.fetchval(
                    "SELECT message_text FROM messages WHERE message_type = 'FIGHT_RESULT_LEGENDARY' ORDER BY random() LIMIT 1"
                )

            # заменяем плейсхолдеры на реальные данные
            fight_result_message = fight_result_message_template.format_map(
                SafeDict(
                    winner_name=winner_name,
                    loser_name=loser_name,
                    winner_weapon=winner_weapon,
                    loser_weapon=loser_weapon,
                    points=points,
                )
            )

            # формируем сообщение о результате дуэли
            result_message = (
                f"@{winner_name}: {winner_balance_after} (+{points}) мл.\n"
                f"@{loser_name}: {loser_balance_after} (-{points}) мл.\n\n"
                f"{fight_result_message}"
            )

            # выбираем случайную гифку для завершения дуэли
            finished_gif_folder = "./media/gifs/duel_finished"
            finished_gifs = [
                os.path.join(finished_gif_folder, file)
                for file in os.listdir(finished_gif_folder)
                if file.endswith(".gif")
            ]
            finished_gif = random.choice(finished_gifs)

            # отправляем случайную гифку с результатом дуэли
            await bot.send_animation(
                chat_id, animation=FSInputFile(finished_gif), caption=result_message
            )

            await connection.execute(
                """
                INSERT INTO fight_history (winner_id, loser_id, points_won, points_lost, telegram_group_id, winner_weapon, loser_weapon)
                VALUES ($1, $2, $3, $3, $4, $5, $6)
                """,
                winner_id,
                loser_id,
                points,
                chat_id,
                winner_weapon,
                loser_weapon
            )

            await connection.execute(
                "UPDATE duel_state SET status = $1 WHERE telegram_group_id = $2 AND id = $3",
                'finished',
                chat_id,
                duel_info["id"],
            )

        except Exception as e:
            logger.error(f"Error in start_duel: {e}")
            await connection.execute(
                "UPDATE duel_state SET status = $1 WHERE telegram_group_id = $2 AND id = $3",
                'error',
                chat_id,
                duel_info["id"],
            )