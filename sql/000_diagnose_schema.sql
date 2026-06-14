-- Диагностика схемы template.
-- psql -h localhost -U roman -d communication -f sql/000_diagnose_schema.sql

\echo '=== template.users ==='
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'template' AND table_name = 'users'
ORDER BY ordinal_position;

\echo '=== template.events ==='
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'template' AND table_name = 'events'
ORDER BY ordinal_position;

\echo '=== pgcrypto ==='
SELECT extname FROM pg_extension WHERE extname = 'pgcrypto';
