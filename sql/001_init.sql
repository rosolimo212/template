-- Схема template: таблицы логирования для шаблона проекта.
-- Выполнить один раз на stage/prod базе от имени пользователя с правами CREATE.

CREATE SCHEMA IF NOT EXISTS template;

CREATE TABLE IF NOT EXISTS template.users (
    user_id BIGSERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    registration_date TIMESTAMP NOT NULL,
    registration_channel TEXT NOT NULL,
    last_active_at TIMESTAMP NOT NULL,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    is_trial BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS template.events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id BIGINT NOT NULL REFERENCES template.users (user_id),
    event_name TEXT NOT NULL,
    channel TEXT NOT NULL,
    event_parameters JSONB,
    inserted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_user_id ON template.events (user_id);
CREATE INDEX IF NOT EXISTS idx_events_event_name ON template.events (event_name);
