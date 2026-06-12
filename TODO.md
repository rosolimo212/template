# TODO-лист проекта

Агрегат задач из комментариев `TODO` в коде. Обновлять по мере разработки.

## Фаза 1 — конфиг
- [x] `config.example.yaml`
- [x] `iter_core/config.py`

## Фаза 2 — postgres-логирование
- [ ] Реализовать `PostgresLogger` (SQLAlchemy + pandas)
- [ ] `allocate_user_id` через postgres sequence

## Фаза 3 — коллекторы
- [ ] `collectors/weather.py` — weatherapi.com
- [ ] `collectors/jokes.py` — чтение `data/jokes.json`

## Фаза 4 — AppService
- [ ] Полный сценарий MVP в `iter_core/app.py` и `brain.py`

## Фаза 5 — UI
- [ ] Streamlit: регистрация, меню, 3 опции
- [ ] Telegram: то же через aiogram
- [ ] Console: полный цикл

## Фаза 6 — тесты
- [ ] Расширить `business_checks.py` по task.md
- [ ] Спецсимволы, логирование событий, upsert users
