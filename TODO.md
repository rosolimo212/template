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
- [ ] `collectors/weather.py` — weatherapi.com
- [ ] `collectors/jokes.py` — чтение `data/jokes.json`

## Фаза 4 — AppService
- [ ] Полный сценарий MVP в `core/app.py` и `brain.py`

## Фаза 5 — UI
- [ ] Streamlit: регистрация, меню, 3 опции
- [ ] Telegram: то же через aiogram
- [ ] Console: полный цикл

## Фаза 6 — тесты
- [ ] Расширить `business_checks.py` по task.md
- [ ] Спецсимволы, логирование событий, upsert users
