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
--rollback ALTER TABLE duel_state DROP COLUMN challenged_weapon;
--rollback ALTER TABLE duel_state DROP COLUMN challenger_weapon;
--rollback ALTER TABLE fight_history DROP COLUMN winner_weapon;
--rollback ALTER TABLE fight_history DROP COLUMN loser_weapon;