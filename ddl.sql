/* удаление таблиц, если они существуют, для обновления структуры */
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS pidor_of_the_day CASCADE;
DROP TABLE IF EXISTS statistics CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS user_balance CASCADE;
DROP TABLE IF EXISTS fight_history CASCADE;
DROP TABLE IF EXISTS duel_state CASCADE;

/* создание таблицы users для хранения информации о пользователях */
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY
    , telegram_id BIGINT UNIQUE NOT NULL
    , username VARCHAR(255)
    , registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
;

/* создание таблицы pidor_of_the_day для хранения информации о выборе пидора дня */
CREATE TABLE pidor_of_the_day (
    id BIGSERIAL PRIMARY KEY
    , user_id BIGINT NOT NULL
    , chosen_at DATE NOT NULL
    , chosen_year INT NOT NULL
    , FOREIGN KEY (user_id) REFERENCES users (id)
)
;

/* создание таблицы statistics для хранения статистики выборов пидоров дня по годам */
CREATE TABLE statistics (
    id BIGSERIAL PRIMARY KEY
    , user_id BIGINT NOT NULL
    , chosen_count INT DEFAULT 0
    , chosen_year INT NOT NULL DEFAULT EXTRACT(YEAR FROM CURRENT_DATE)
    , FOREIGN KEY (user_id) REFERENCES users (id)
    , CONSTRAINT unique_user_year UNIQUE (user_id, chosen_year)
)
;

/* создание таблицы messages для хранения текстов сообщений */
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY
    , message_text TEXT NOT NULL
    , message_order INT NOT NULL
    , message_type VARCHAR(50) NOT NULL
    , scenario_id INT NOT NULL
)
;

/* создание таблицы для хранения баланса semen пользователей */
CREATE TABLE user_balance (
    user_id BIGINT PRIMARY KEY
    , points INT DEFAULT 500
    , FOREIGN KEY (user_id) REFERENCES users (id)
)
;

/* создание таблицы для хранения истории боев */
CREATE TABLE fight_history (
    id BIGSERIAL PRIMARY KEY
    , winner_id BIGINT NOT NULL
    , loser_id BIGINT NOT NULL
    , points_won INT NOT NULL
    , points_lost INT NOT NULL
    , battle_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    , FOREIGN KEY (winner_id) REFERENCES users (id)
    , FOREIGN KEY (loser_id) REFERENCES users (id)
)
;

/* создание таблицы для хранения состояния схваток */
CREATE TABLE duel_state (
    id BIGSERIAL PRIMARY KEY,
    challenger_id BIGINT NOT NULL,
    challenged_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    weapon_chosen_challenger INT,
    weapon_chosen_challenged INT,
    FOREIGN KEY (challenger_id) REFERENCES users (id),
    FOREIGN KEY (challenged_id) REFERENCES users (id)
)
;


-- Наполнение базы + корректирующие скрипты
/*ALTER DATABASE postgres SET timezone TO 'UTC';*/

ALTER TABLE duel_state
ALTER COLUMN created_at SET DATA TYPE TIMESTAMP WITH TIME ZONE
USING created_at AT TIME ZONE 'UTC'
;


INSERT INTO messages (message_text, message_order, message_type, scenario_id)
VALUES 
    ('Инициирую поиск пидора дня...', 1, 'INIT', 1)
    , ('Военный спутник запущен, коды доступа внутри...', 2, 'INIT', 1)
    , ('Высокий приоритет мобильному юниту.', 3, 'INIT', 1)
    , ('Поиск начат, готовьте оружие...', 1, 'INIT', 2)
    , ('Спутник на орбите, данные обрабатываются...', 2, 'INIT', 2)
    , ('Цель найдена, укажите координаты.', 3, 'INIT', 2)
    , ('Осторожно! Пидор дня активирован!', 1, 'INIT', 3)
    , ('Интересно...', 2, 'INIT', 3)
    , ('Что с нами стало...', 3, 'INIT', 3)
    , ('Осторожно! Пидор дня активирован!', 1, 'INIT', 4)
    , ('Военный спутник запущен, коды доступа внутри...', 2, 'INIT', 4)
    , ('Ведётся захват подозреваемого...', 3, 'INIT', 4)
    /*  */
    , ('Ого, вы посмотрите только! А пидор дня то {username}', -1, 'RESULT', 2)
    , ('Няшный пидор дня - {username}', -1, 'RESULT', 3)
    , ('Кто бы мог подумать, но пидор дня - {username}', -1, 'RESULT', 4)
    , ('Ага! Поздравляю! Сегодня ты пидор {username}', -1, 'RESULT', 5)
    , ('Ну ты и пидор, {username}', -1, 'RESULT', 6)
    , ('''
​ .∧＿∧
( ･ω･｡)つ━☆・*。
⊂  ノ    ・゜+.
しーＪ   °。+ *´¨)
    .· ´¸.·*´¨)
    (¸.·´ (¸.·"* ☆ ВЖУХ И ТЫ ПИДОР, {username}
    ''', -1, 'RESULT', 1
    )
;
