--liquibase formatted sql
--changeset naensamble:fight_status
ALTER TABLE duel_state
ADD COLUMN status TEXT
;
--rollback ALTER TABLE duel_state DROP COLUMN status;