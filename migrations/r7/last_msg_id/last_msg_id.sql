--liquibase formatted sql
--changeset naensamble:last_msg_id
ALTER TABLE duel_state
ADD COLUMN last_message_id BIGINT
;
--rollback ALTER TABLE duel_state DROP COLUMN last_message_id;