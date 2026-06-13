# TODO-лист проекта

Агрегат задач из комментариев `TODO` в коде. Обновлять по мере разработки.

## Фаза 1 — конфиг
- [x] `config.example.yaml`
- [x] `core/config.py`
- [x] `core/db.py`

## Фаза 2 — postgres-логирование
- [x] Реализовать `PostgresLogger` (SQLAlchemy + pandas)
- [x] `allocate_user_id` через postgres sequence

## Фаза 3 — коллекторы
- [x] `collectors/weather.py` — weatherapi.com
- [x] `collectors/jokes.py` — чтение `data/jokes.json`

## Фаза 4 — AppService
- [x] Полный сценарий MVP в `core/app.py` и `brain.py`

## Фаза 5 — UI
- [x] Streamlit: регистрация, меню, 3 опции
- [x] Telegram: то же через aiogram
- [x] Console: полный цикл

## Фаза 6 — тесты
- [x] Расширить `business_checks.py` по task.md
- [x] Спецсимволы, логирование событий, upsert users

cd /home/roman/python/kotelok/template
./pre_commit_check.sh
