--liquibase formatted sql
--changeset Zhuravkok.A.A:fix_duel_state
ALTER TABLE duel_state
ALTER COLUMN challenged_id DROP NOT NULL;
--rollback ALTER TABLE duel_state
--rollback ALTER COLUMN challenged_id SET NOT NULL;