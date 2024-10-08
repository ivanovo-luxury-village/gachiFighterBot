--liquibase formatted sql
--changeset naensamble:weapon
ALTER TABLE duel_state
ADD COLUMN challenger_weapon TEXT,
ADD COLUMN challenged_weapon TEXT 
;
ALTER TABLE fight_history
ADD COLUMN winner_weapon TEXT, 
ADD COLUMN loser_weapon TEXT
;
INSERT INTO messages (message_text, message_order, message_type, scenario_id)
VALUES 
('{loser_weapon} у {loser_name} оказался как у настоящего ♂slaves♂. Такой ♂dungeon master♂ как {winner_name} не прощает бедного ⚣jabroni⚣. {loser_name} нужно чаще посещать ♂gym♂'
    , -1, 'FIGHT_RESULT', 1)
, ('{loser_name}, дружок пирожок, кажется ты ошибся дверью, клуб для ♂slaves♂ на 2 блока ниже'
    , -1, 'FIGHT_RESULT', 2)
, ('{winner_name} Вот это ты дал используя {winner_weapon}, все в semen, {loser_name} обесчестен, у него стало на {points} мл. меньше ⚣semen⚣ и сломанный {loser_weapon}'
    , -1, 'FIGHT_RESULT', 3)
, ('У {loser_name} {loser_weapon} из стали, но у {winner_name} {winner_weapon} из алмаза! {winner_name} забирает у {loser_name} {points} мл. ⚣semen⚣.'
    , -1, 'FIGHT_RESULT', 4)
, ('{winner_name} проводит болевой на {loser_weapon} бедного ⚣jabroni⚣ {loser_name}'
    , -1, 'FIGHT_RESULT', 5)
, ('{loser_name} не ожидал такой резкой атаки с помощью {winner_weapon} от {winner_name}. {loser_name} опустошен на {points} мл. ⚣semen⚣.'
    , -1, 'FIGHT_RESULT', 6)
, ('Ебать ты! Все белое! {winner_name} доказал, что он ⚣man⚣. Умело используя {winner_weapon} он лишает {loser_name} {points} мл. ⚣semen⚣.'
    , -1, 'FIGHT_RESULT', 7)
, ('Уууу слабовато дружок пирожок.... {winner_name} провел битву в духе ♂slaves♂. Такого стыдного опустощения никто не ожидал. {winner_name} всего лишь опустошил {loser_name} на {points} мл. ⚣semen⚣.'
    , -1, 'FIGHT_RESULT_WEAK', 1)
, ('Неплохая защита {loser_name} от {winner_weapon}. {loser_weapon} у {loser_name} что надо. {loser_name} показал что он не легкая добыча для любого ⚣man⚣, особенно такого как {winner_name}. Но {loser_name} все-таки не удержал и потерял {points} мл. ⚣semen⚣.'
    , -1, 'FIGHT_RESULT_WEAK', 2)
, ('ОГО! Какую легендарную комбинацию выдал {winner_name}. Великолепный приём в стиле ⚣cum on your {winner_weapon}⚣ будут помнить все ⚣jabroni⚣ еще ни один год. Я бы посоветовал {loser_name} бежать за салфетками и ⚣recovery semen⚣'
    , -1, 'FIGHT_RESULT_LEGENDARY', 1)
--rollback ALTER TABLE duel_state DROP COLUMN challenged_weapon;
--rollback ALTER TABLE duel_state DROP COLUMN challenger_weapon;
--rollback ALTER TABLE fight_history DROP COLUMN winner_weapon;
--rollback ALTER TABLE fight_history DROP COLUMN loser_weapon;
--rollback DELETE FROM messages WHERE message_type IN ('FIGHT_RESULT_WEAK', 'FIGHT_RESULT', 'FIGHT_RESULT_LEGENDARY')