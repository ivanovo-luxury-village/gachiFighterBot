--liquibase formatted sql
--changeset naensamble:add_col_duel_type
ALTER TABLE duel_state
ADD COLUMN duel_type TEXT;
UPDATE duel_state SET duel_type = 'specific' WHERE challenged_id IS NOT NULL;
UPDATE duel_state SET duel_type = 'open' WHERE challenged_id IS NULL;
--rollback ALTER TABLE duel_state DROP COLUMN duel_type;