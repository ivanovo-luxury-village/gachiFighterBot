--liquibase formatted sql
--changeset naensamble:debts
CREATE TABLE debts (
    id BIGSERIAL PRIMARY KEY
    , telegram_group_id BIGINT NOT NULL
    , debtor_id BIGINT NOT NULL 
    , creditor_id BIGINT NOT NULL
    , debt_sum INT
    , status VARCHAR(255)
    , created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
--rollback DROP TABLE IF EXISTS debts;