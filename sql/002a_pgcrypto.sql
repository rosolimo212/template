-- Шаг 1: расширение pgcrypto (нужно для sha256 при миграции).
-- Запускать от системного postgres (не от roman):
--
--   cd /tmp
--   cat .../sql/002a_pgcrypto.sql | sudo -u postgres psql -d communication

CREATE EXTENSION IF NOT EXISTS pgcrypto;
