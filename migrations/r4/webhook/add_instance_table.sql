--liquibase formatted sql
--changeset Zhuravkov.A.A:add_instance_table
CREATE TABLE IF NOT EXISTS bot_instance (
  id BIGSERIAL PRIMARY KEY,
  bot_instance_count BIGINT NOT NULL,
  webhook_url VARCHAR(255),
  updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO bot_instance(bot_instance_count, webhook_url, updated_At)
VALUES (0, '', NOW());
--rollback DROP TABLE IF EXISTS bot_instance;