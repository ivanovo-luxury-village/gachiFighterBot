--liquibase formatted sql
--changeset naensamble:updated_at
ALTER TABLE duel_state
ADD COLUMN updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
;
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS '
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
' LANGUAGE plpgsql
;
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON duel_state
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column()
;
--rollback DROP TRIGGER IF EXISTS set_updated_at ON duel_state;
--rollback DROP FUNCTION IF EXISTS update_updated_at_column();
--rollback ALTER TABLE duel_state DROP COLUMN updated_at;