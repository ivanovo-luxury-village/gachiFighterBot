--liquibase formatted sql
--changeset naensamble:new_texts
INSERT INTO messages (message_text, message_order, message_type, scenario_id)
VALUES
('♂Billy♂ свидетель, это был страшный бой... Но тем не менее, {winner_name} смог одолеть {loser_name}, хотя сам чуть не потерпел поражение...'
    , -1, 'FIGHT_RESULT', 8)
, ('Великолепная атака от {winner_name}! Поимел {loser_name} как надо, тому ничего не остаётся, кроме как молить на коленях о прощении!'
    , -1, 'FIGHT_RESULT', 9)
, ('{loser_name} руководствуется принципами A.C.A.B. — Always Cumshot After Blowjob. Иначе невозможно объяснить, как он так жёстко отсосал {winner_name}... Кажется, его ♂{loser_weapon}♂ слишком слаб для таких битв...'
    , -1, 'FIGHT_RESULT', 10)
, ('Тяжёлый бой, бой равных и сильных, но ♂{winner_weapon}♂ {winner_name} оказался сильнее. Задница {loser_name} как следует трахнута и ему показали его место!'
    , -1, 'FIGHT_RESULT', 11)
, ('Если бы Супермен встретился с {winner_name}, то потерял бы всю свою силу от его криптонитового хуя. Что уж говорить о {loser_name}... его превратили в сперматозоидную пыль страшным ♂{winner_weapon}♂'
    , -1, 'FIGHT_RESULT', 12)
, ('У {winner_name} ♂{winner_weapon}♂ из титана, а у {loser_name} как будто из фантиков. Кто ж с таким оружием на бой выходит? Отправляйся-ка в клетку, ♂college boy♂, там тебе самое место, ♂fucking slave♂'
    , -1, 'FIGHT_RESULT', 13)
, ('За такую схватку каждый из ♂jabrone♂ достоин наград. {winner_name} получает медаль «За атаку хуй в сраку», {loser_name} получит Орден Вана Даркхолма'
    , -1, 'FIGHT_RESULT', 14)
, ('Борьба была равна, боролись два... двое настоящих мужчин! С небольшим перевесом, буквально на последних каплях ♂semen♂ {winner_name} побеждает {loser_name}!'
    , -1, 'FIGHT_RESULT_WEAK', 3)
, ('ОХУЕТЬ! {winner_name} проводит просто безбожный болевой на ♂{loser_weapon}♂ {loser_name}, заставляя того молить о пощаде! Ещё одна такая победа и {loser_name} пойдёт заниматься сексом с женщинами!'
    , -1, 'FIGHT_RESULT_LEGENDARY', 2)
, ('ЛЕГЕНДАРНАЯ КОМБИНАЦИЯ ОТ {winner_name}! Абсолютное cum-bo самых жутких ударов, какие только существуют на свете! {loser_name} повержен, обоссан, унижен, опущен, а об его лицо победитель {winner_name} просто вытер свой член, как об салфетку....'
    , -1, 'FIGHT_RESULT_LEGENDARY', 3)
--rollback DELETE FROM messages WHERE message_type = 'FIGHT_RESULT' AND scenario_id BETWEEN 8 AND 14;
--rollback DELETE FROM messages WHERE message_type = 'FIGHT_RESULT_WEAK' AND scenario_id = 3;
--rollback DELETE FROM messages WHERE message_type = 'FIGHT_RESULT_LEGENDARY' AND scenario_id BETWEEN 2 AND 3;