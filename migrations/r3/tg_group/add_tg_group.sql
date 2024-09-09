--liquibase formatted sql
--changeset naensamble:add_tg_group
ALTER TABLE users
DROP CONSTRAINT IF EXISTS users_telegram_id_key
;
ALTER TABLE users
ADD COLUMN telegram_group_id BIGINT
;
CREATE UNIQUE INDEX unique_telegram_user_group ON users (telegram_id, telegram_group_id)
;
ALTER TABLE pidor_of_the_day
ADD COLUMN telegram_group_id BIGINT
;
CREATE UNIQUE INDEX unique_pidor_group ON pidor_of_the_day (user_id, chosen_at, telegram_group_id)
;
ALTER TABLE statistics
ADD COLUMN telegram_group_id BIGINT
;
CREATE UNIQUE INDEX unique_statistics_group ON statistics (user_id, chosen_year, telegram_group_id)
;
ALTER TABLE user_balance
ADD COLUMN telegram_group_id BIGINT
;
CREATE UNIQUE INDEX unique_user_balance_group ON user_balance (user_id, telegram_group_id)
;
ALTER TABLE fight_history
ADD COLUMN telegram_group_id BIGINT
;
ALTER TABLE duel_state
ADD COLUMN telegram_group_id BIGINT
;
--rollback ALTER TABLE users DROP COLUMN telegram_group_id;
--rollback DROP INDEX IF EXISTS unique_telegram_user_group;
--rollback ALTER TABLE pidor_of_the_day DROP COLUMN telegram_group_id;
--rollback DROP INDEX IF EXISTS unique_pidor_group;
--rollback ALTER TABLE statistics DROP COLUMN telegram_group_id;
--rollback DROP INDEX IF EXISTS unique_statistics_group;
--rollback ALTER TABLE user_balance DROP COLUMN telegram_group_id;
--rollback DROP INDEX IF EXISTS unique_user_balance_group;
--rollback ALTER TABLE fight_history DROP COLUMN telegram_group_id;
--rollback ALTER TABLE duel_state DROP COLUMN telegram_group_id;