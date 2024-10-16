--liquibase formatted sql
--changeset naensamble:new_fight_texts
INSERT INTO messages (message_text, message_order, message_type, scenario_id)
VALUES
('Жалкий {loser_name} повержен страшным {winner_weapon} {winner_name}. Чтобы процесс доминирования считался завершённым, {winner_name} обоссал с ног до головы поверженного противника... {loser_name} не осталось ничего, кроме как терпеть и ждать реванша'
    , -1, 'FIGHT_RESULT', 15)
, ('{winner_name} не просто одолел {loser_name}, всё куда хуже. {loser_name} теперь абсолютно официально самый жалкий ♂S L A V E♂ — его новый ♂FULL MASTER♂ сможет делать со своей вещью всё, что угодно. Но держу пари, что ♂ass♂ {loser_name} будет продана на гачи-рынок рабов по красной цене в $300... Одному только Billy известно, какие ужасы предстоит пережить новоиспечённому ♂slave♂ ....'
    , -1, 'FIGHT_RESULT', 16)
, ('Настоящий фистинговый хоровод развернулся в одной из ивановских ♂gym♂. {winner_name} нанёс {loser_name} тысячи ударов, но тот стойко вытерпел даже самые сильные из них — даже удары конской залупы {winner_name} по лицу и его {winner_weapon}. Он выстоял, однако единогласным решением судей проиграл бой — но не войну! Букмекеры уже собирают ставки по ♂300 bucks♂ на реванш...'
    , -1, 'FIGHT_RESULT', 17)
, ('Такие жестокие заломы и болевые приёмы не испытывал на себе даже ♂Van Darkholm♂. {winner_name} просто на атомы разложил {loser_name}, лишив его не только ♂semen♂, но и потенциала бороться дальше — после такого поражения многие не восстанавливаются никогда...'
    , -1, 'FIGHT_RESULT', 18)
, ('Тяжёлая борьба двух потных дел продолжалась все сутки, а запасы вазелина и массажного масла закончились во всех районных магазинах и аптеках. Такому накалу страстей двух мужчин позавидуют даже атлеты турецкой борьбы Кирпкинар.... Тем не менее, {winner_name} всё же смог с небольшим перевесом победить {loser_name} с помощью своего стального {winner_weapon}'
    , -1, 'FIGHT_RESULT_WEAK', 4)
;
--rollback DELETE FROM messages WHERE message_type = 'FIGHT_RESULT' AND scenario_id BETWEEN 15 AND 18;
--rollback DELETE FROM messages WHERE message_type = 'FIGHT_RESULT_WEAK' AND scenario_id = 4;