--liquibase formatted sql
--changeset naensamble:slap
CREATE TABLE slaps (
    id BIGSERIAL PRIMARY KEY
    , telegram_group_id BIGINT NOT NULL
    , slapper_user_id BIGINT NOT NULL 
    , target_user_id BIGINT NOT NULL
    , points_deducted INT
    , slap_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
--rollback DROP TABLE IF EXISTS slap;