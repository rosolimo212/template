-- Права роли tester на схему template.
-- Подключайтесь к базе communication от roman:
--   psql -h localhost -U roman -d communication -f sql/002_grants_tester.sql
--
-- GRANT CONNECT на базу выполняется в shell-скрипте отдельно.

GRANT USAGE ON SCHEMA template TO tester;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA template TO tester;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA template TO tester;

ALTER DEFAULT PRIVILEGES FOR ROLE roman IN SCHEMA template
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tester;
ALTER DEFAULT PRIVILEGES FOR ROLE roman IN SCHEMA template
    GRANT USAGE, SELECT ON SEQUENCES TO tester;
