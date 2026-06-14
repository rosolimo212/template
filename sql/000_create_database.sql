-- Создание базы communication (один раз на сервере, от roman).
-- psql -h localhost -U roman -d postgres -f sql/000_create_database.sql

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'communication' AND pid <> pg_backend_pid();

-- Раскомментируйте DROP, если пересоздаёте базу с нуля:
-- DROP DATABASE IF EXISTS communication;

CREATE DATABASE communication OWNER roman;
