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
VALUES ('текст', -1, 'FIGHT_RESULT', 1)
, ('текст', -1, 'FIGHT_RESULT', 2)
, ('текст', -1, 'FIGHT_RESULT', 3)
, ('текст', -1, 'FIGHT_RESULT', 4)
, ('текст', -1, 'FIGHT_RESULT', 5)
, ('текст', -1, 'FIGHT_RESULT', 6)
, ('текст', -1, 'FIGHT_RESULT', 7)
, ('текст', -1, 'FIGHT_RESULT', 8)
, ('текст', -1, 'FIGHT_RESULT', 9)
, ('текст', -1, 'FIGHT_RESULT', 10)
--rollback ALTER TABLE duel_state DROP COLUMN challenged_weapon;
--rollback ALTER TABLE duel_state DROP COLUMN challenger_weapon;
--rollback ALTER TABLE fight_history DROP COLUMN winner_weapon;
--rollback ALTER TABLE fight_history DROP COLUMN loser_weapon;