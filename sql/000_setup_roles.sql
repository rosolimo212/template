-- Создание ролей postgres.
-- Выполнять от системного суперпользователя postgres:
--   cd /tmp
--   cat /home/roman/python/kotelok/template/sql/000_setup_roles.sql | sudo -u postgres psql
--
-- Пароль roman задаётся вручную после этого скрипта:
--   sudo -u postgres psql
--   \password roman
--
-- Пароль root (при необходимости):
--   \password root

-- root — суперпользователь БД (аналог админа на VM)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'root') THEN
        CREATE ROLE root WITH LOGIN SUPERUSER CREATEDB CREATEROLE;
    ELSE
        ALTER ROLE root WITH SUPERUSER CREATEDB CREATEROLE;
    END IF;
END
$$;

-- roman — владелец stage-базы, создаёт схемы и таблицы
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'roman') THEN
        CREATE ROLE roman WITH LOGIN CREATEDB;
    ELSE
        ALTER ROLE roman WITH CREATEDB;
    END IF;
END
$$;

-- tester — роль для тестов на stage (пароль фиксированный для локали)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'tester') THEN
        CREATE ROLE tester WITH LOGIN PASSWORD '123456';
    ELSE
        ALTER ROLE tester WITH LOGIN PASSWORD '123456';
    END IF;
END
$$;
