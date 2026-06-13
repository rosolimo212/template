-- Миграция: user_id BIGINT -> user_id TEXT (hash) + internal_user_id + external_user_id
--
-- Порядок:
--   1. sql/002a_pgcrypto.sql  (от postgres)
--   2. sql/000_diagnose_schema.sql  (проверка)
--   3. этот файл (от roman)
--
--   psql -h localhost -U roman -d iter_template_stage -f sql/002_migrate_user_ids.sql

\set ON_ERROR_STOP on

DO $$
DECLARE
    has_internal boolean;
    user_id_type text;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'template' AND table_name = 'users'
          AND column_name = 'internal_user_id'
    ) INTO has_internal;

    IF has_internal THEN
        RAISE NOTICE 'Миграция уже выполнена: internal_user_id существует';
        RETURN;
    END IF;

    SELECT data_type INTO user_id_type
    FROM information_schema.columns
    WHERE table_schema = 'template' AND table_name = 'users'
      AND column_name = 'user_id';

    IF user_id_type IS DISTINCT FROM 'bigint' THEN
        RAISE EXCEPTION 'Неожиданный тип template.users.user_id: % (ожидался bigint)', user_id_type;
    END IF;

    RAISE NOTICE 'Мигрируем template.users ...';

    -- Сначала снимаем FK с events, иначе users_pkey не удалить
    ALTER TABLE template.events DROP CONSTRAINT IF EXISTS events_user_id_fkey;

    ALTER TABLE template.users RENAME COLUMN user_id TO internal_user_id;

    ALTER TABLE template.users ADD COLUMN external_user_id TEXT;
    ALTER TABLE template.users ADD COLUMN user_id TEXT;

    UPDATE template.users
    SET
        external_user_id = 'legacy-' || internal_user_id::text,
        user_id = encode(
            digest(
                registration_channel || ':' || ('legacy-' || internal_user_id::text),
                'sha256'
            ),
            'hex'
        );

    ALTER TABLE template.users ALTER COLUMN external_user_id SET NOT NULL;
    ALTER TABLE template.users ALTER COLUMN user_id SET NOT NULL;

    ALTER TABLE template.users DROP CONSTRAINT IF EXISTS users_pkey;
    ALTER TABLE template.users ADD PRIMARY KEY (user_id);

    CREATE UNIQUE INDEX IF NOT EXISTS users_internal_user_id_uidx
        ON template.users (internal_user_id);

    RAISE NOTICE 'Мигрируем template.events ...';

    ALTER TABLE template.events ADD COLUMN IF NOT EXISTS user_id_new TEXT;
    ALTER TABLE template.events ADD COLUMN IF NOT EXISTS internal_user_id BIGINT;
    ALTER TABLE template.events ADD COLUMN IF NOT EXISTS external_user_id TEXT;

    UPDATE template.events e
    SET
        internal_user_id = e.user_id,
        user_id_new = u.user_id,
        external_user_id = u.external_user_id
    FROM template.users u
    WHERE e.user_id = u.internal_user_id;

    ALTER TABLE template.events DROP COLUMN user_id;
    ALTER TABLE template.events RENAME COLUMN user_id_new TO user_id;

    ALTER TABLE template.events ALTER COLUMN user_id SET NOT NULL;
    ALTER TABLE template.events ALTER COLUMN internal_user_id SET NOT NULL;
    ALTER TABLE template.events ALTER COLUMN external_user_id SET NOT NULL;

    ALTER TABLE template.events
        ADD CONSTRAINT events_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES template.users (user_id);

    DROP INDEX IF EXISTS template.idx_events_user_id;
    CREATE INDEX IF NOT EXISTS idx_events_user_id ON template.events (user_id);
    CREATE INDEX IF NOT EXISTS idx_events_internal_user_id ON template.events (internal_user_id);
    CREATE INDEX IF NOT EXISTS idx_users_external_user_id ON template.users (external_user_id);

    RAISE NOTICE 'Миграция завершена успешно';
END $$;
