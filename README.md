# Template — modular Python service starter

Reusable project skeleton: one core, swappable UI and logging. MVP flow: ask name → main menu (weather, joke, diary) with PostgreSQL event logging.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  UI clients (swappable via config.yaml app.interface)       │
│  streamlit  │  telegram (aiogram)  │  console               │
└──────────────────────────┬──────────────────────────────────┘
                           │ identity, action, payload
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AppService (core/app.py)                                   │
│  orchestrates scenario, calls brain + collectors + logger   │
└───────┬─────────────────────┬─────────────────────┬─────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ brain         │   │ collectors      │   │ logging          │
│ screens,      │   │ weather, jokes  │   │ postgres / noop  │
│ AppResponse   │   │ external APIs   │   │ users + events   │
└───────────────┘   └─────────────────┘   └──────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ data/dialog_messages.json — all user-visible texts            │
└─────────────────────────────────────────────────────────────┘
```

**Data flow**

1. UI calls `handle_start` or `handle_action(identity, channel, action, payload)`.
2. `AppService` updates users/events via `EventLogger`, runs collectors when needed.
3. `brain` returns `AppResponse` (text, buttons, next `Screen`).
4. UI shows the response via `apply_response()` in `ui/helpers.py`.

**Key types**

| Type | Role |
|------|------|
| `UserIdentity` | `user_id` (hash PK), `internal_user_id`, `external_user_id` |
| `AppResponse` | What to show the user after one scenario step |
| `payload` | Dict passed to `handle_action`: `text`, `screen`, `user_name`, … |
| `Screen` | FSM screen: `start`, `main_menu`, `diary_wait`, … |

---

## Stack

- Python 3.10+
- UI: Streamlit, aiogram 3, console
- Logging: PostgreSQL (schema `template` in database `communication`), optional noop
- Config: `config.yaml` (gitignored)
- User texts: `data/dialog_messages.json`

---

## Database layout

Same names on **stage** (local) and **prod** (VM); data is separated by different servers.

| Level | Name |
|-------|------|
| Database | `communication` |
| Schema (first service) | `template` |
| Tables | `template.users`, `template.events` |

More services → new schemas in `communication` with the same table pattern.

Setup:

```bash
./scripts/setup_postgres.sh
```

---

## Configuration

Copy `config.example.yaml` → `config.yaml`:

```yaml
app:
  interface: streamlit   # streamlit | telegram | console
  logging_enabled: true

logging:
  database: communication
  schema: template
  user: roman
  password: "..."

telegram:
  token: "..."
  # proxy: "socks5://host:port"   # if API unreachable (e.g. RU VPS)

weatherapi:
  api_key: "..."
```

---

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Streamlit (separate command)
streamlit run ui/streamlit_app.py

# Telegram or console
python main.py
```

Tests:

```bash
./pre_commit_check.sh
```

---

## User texts & localization

All dialogs live in `data/dialog_messages.json`:

- `messages` — full phrases (with `{placeholders}`)
- `buttons` — menu and action labels
- Fields: `name`, `id`, `when` (when user sees it), `default`, `console`, `telegram`, `browser`
- Empty channel field → use `default`

Edit JSON, not Python, to change copy. Code loads texts via `core/messages.py`.

**Streamlit returning users:** browser cookie `template_browser_session` stores `external_user_id`, screen, and name (365 days). Requires `extra-streamlit-components` (see `requirements.txt`). After deploy: `pip install -r requirements.txt` and restart Streamlit.

---

## Branches

- `dev` — local development
- `main` — production on VM

```bash
git checkout main && git merge dev && git push origin main
```

---

## Project layout

```
core/           brain, app, models, db, messages, collectors, logging
ui/             streamlit, telegram, console, helpers
data/           dialog_messages.json, jokes.json
sql/            postgres setup and migrations
scripts/        setup_postgres.sh, migrate_user_ids.sh
tests/          pytest
business_checks.py   layer-2 checks
```

---

# Шаблон — модульный стартовый Python-сервис

Заготовка для других проектов: одно ядро, сменяемые UI и логирование. MVP: имя → главное меню (погода, анекдот, дневник) + логи в PostgreSQL.

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│  UI-клиенты (переключение в config.yaml app.interface)      │
│  streamlit  │  telegram (aiogram)  │  console               │
└──────────────────────────┬──────────────────────────────────┘
                           │ identity, action, payload
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AppService (core/app.py)                                   │
│  сценарий, brain + collectors + logger                      │
└───────┬─────────────────────┬─────────────────────┬─────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ brain         │   │ collectors      │   │ logging          │
│ экраны,       │   │ погода, анекдоты│   │ postgres / noop  │
│ AppResponse   │   │ внешние API     │   │ users + events   │
└───────────────┘   └─────────────────┘   └──────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ data/dialog_messages.json — все тексты для пользователя       │
└─────────────────────────────────────────────────────────────┘
```

**Поток данных**

1. UI вызывает `handle_start` или `handle_action(identity, channel, action, payload)`.
2. `AppService` пишет в users/events, при необходимости дергает коллекторы.
3. `brain` возвращает `AppResponse` (текст, кнопки, следующий `Screen`).
4. UI показывает ответ через `apply_response()` в `ui/helpers.py`.

**Ключевые сущности**

| Сущность | Назначение |
|----------|------------|
| `UserIdentity` | `user_id` (hash PK), `internal_user_id`, `external_user_id` |
| `AppResponse` | Что показать пользователю после одного шага сценария |
| `payload` | Словарь для `handle_action`: `text`, `screen`, `user_name`, … |
| `Screen` | Экран FSM: `start`, `main_menu`, `diary_wait`, … |

---

## Стек

- Python 3.10+
- UI: Streamlit, aiogram 3, консоль
- Логи: PostgreSQL (схема `template` в базе `communication`), можно отключить
- Конфиг: `config.yaml` (не в git)
- Тексты: `data/dialog_messages.json`

---

## База данных

Одинаковые имена на **stage** (локально) и **prod** (VM); данные разделены разными серверами.

| Уровень | Имя |
|---------|-----|
| База | `communication` |
| Схема (первый сервис) | `template` |
| Таблицы | `template.users`, `template.events` |

Новые сервисы → новые схемы в `communication` по тому же шаблону.

Установка:

```bash
./scripts/setup_postgres.sh
```

---

## Конфигурация

Скопируйте `config.example.yaml` → `config.yaml` (см. английскую секцию выше).

---

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

streamlit run ui/streamlit_app.py
python main.py
```

Тесты:

```bash
./pre_commit_check.sh
```

---

## Тексты и локализация

Все диалоги в `data/dialog_messages.json`:

- `messages` — фразы (`{плейсхолдеры}`)
- `buttons` — подписи кнопок
- Поля: `name`, `id`, `when` (когда видит пользователь), `default`, `console`, `telegram`, `browser`
- Пустое поле канала → берётся `default`

Правки текстов — в JSON, код читает через `core/messages.py`.

**Streamlit — повторный визит:** cookie `template_browser_session` хранит `external_user_id`, экран и имя (365 дней). Нужен пакет `extra-streamlit-components` (`pip install -r requirements.txt`), перезапуск Streamlit после обновления.

---

## Ветки

- `dev` — разработка локально
- `main` — прод на VM

```bash
git checkout main && git merge dev && git push origin main
```

---

## Структура проекта

```
core/           brain, app, models, db, messages, collectors, logging
ui/             streamlit, telegram, console, helpers
data/           dialog_messages.json, jokes.json
sql/            postgres
scripts/        setup_postgres.sh
tests/          pytest
business_checks.py
```

---

## Подключение к postgres

Предпочтительно:

```python
from core.db import postgres_connection

with postgres_connection(logging_config) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
```

Соединение закрывается в `finally`, при успехе — `commit`, при ошибке — `rollback`.
