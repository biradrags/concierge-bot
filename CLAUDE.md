# Concierge Bot — инструкции для Claude Code

Канон — локальный воркспейс (`~/Desktop/home/.claude/rules/`); cloud-сессии канона не видят — только точечные багфиксы, не трогать деньги/миграции/webhook-гейты.

---

## Референс проект

**Всё копируем из metrika-bot и точечно правим под hotel-архитектуру.**
Путь к референсу: `../metrika-bot`

Вместо генерации с нуля — `cp`, затем точечное обновление контента:
```bash
cp ../metrika-bot/pyproject.toml .
cp ../metrika-bot/scripts/run_tests.sh scripts/
cp ../metrika-bot/tests/conftest.py tests/
# и т.д.
```

---

## Контекст проекта

Telegram concierge bot для отелей и вилл на Бали.

**Мультитенантность:**
- Центральный admin-бот: отели регистрируются, настраивают сервисы
- Каждый отель получает своего бота для гостей
- Гость → бот → сервисы (рестораны, туры, трансфер) → бронирование → оплата провайдеру → комиссия платформе

**Стек:** Python 3.12, aiogram 3.x, aiogram_dialog, SQLAlchemy + asyncpg, PostgreSQL 16, dishka DI, uv, Fly.io

**Fly.io приложения:** не созданы — проект не развёрнут (см. «Деплой»). Имена, заложенные в `fly.toml`: `bali-concierge` (бот), `bali-concierge-db` (PostgreSQL).

---

## Структура проекта (по аналогии с metrika-bot)

```
concierge-bot/
├── concierge_bot/
│   ├── __init__.py
│   ├── __main__.py           # точка входа (webhook)
│   ├── config.py             # pydantic-settings
│   ├── main_factory.py       # фабрика приложения
│   ├── db/
│   │   ├── base.py           # Base, TimestampMixin
│   │   └── models.py         # ORM модели
│   ├── dao/
│   │   ├── holder.py         # HolderDao
│   │   ├── hotel.py
│   │   ├── guest.py
│   │   ├── service.py
│   │   └── booking.py
│   ├── dto/                  # Pydantic DTO
│   ├── services/             # use-cases (бизнес-логика)
│   ├── di/                   # Dishka providers
│   ├── tgbot/
│   │   ├── handlers/
│   │   ├── dialogs/
│   │   ├── filters/
│   │   └── middlewares/
│   ├── migrations/           # alembic
│   └── utils/
├── tests/
│   ├── unit/
│   └── integration/          # e2e не заведён — нет userbot-контура в этом проекте
├── scripts/
│   ├── rules_check.py        # семантические проверки (Decimal и т.д.)
│   └── seed.py
├── .github/workflows/
│   └── fly-deploy.yml
├── Dockerfile
├── fly.toml
├── pyproject.toml            # pytest-конфиг - [tool.pytest.ini_options] здесь же
├── alembic.ini
└── uv.lock                   # генерируется через uv sync
```

---

## Модели БД (hotel-архитектура)

ORM-модели: `concierge_bot/db/models.py` (Hotel, Service, Guest, Booking).

---

## Config (по аналогии с metrika/config.py)

- Копируй `metrika/config.py` → убери metrika-специфику → адаптируй поля
- Обязательные поля в `ProductionConfig`: `TELEGRAM_BOT_TOKEN`
- `get_config()` — тот же паттерн: `APP_ENV` → нужный класс

---

## Dependencies (uv-style)

```bash
uv sync
uv sync --extra test
uv sync --extra lint

# НЕ использовать pip напрямую
```

Запуск бота/тестов/миграций — через Make (см. «Команды (Make)» ниже), не голый `uv run`.

---

## Деплой

**Проект НЕ развёрнут** (решение Ивана 2026-08-12): приложений `bali-concierge` / `bali-concierge-db` на Fly не существует, репозиторий живёт как образец архитектуры. Деплой-workflow снят — он падал с апреля 2026 (`FLY_API_TOKEN` в секретах репо пустой) и держал CI красным без пользы.

Если проект оживёт: завести приложения на Fly (org `personal`), вернуть `.github/workflows/fly-deploy.yml` по образцу metrika-bot, задать секрет, добавить `release_command = 'alembic upgrade head'` в `fly.toml` (сейчас его нет — открытый gap). Команды после этого стандартные: `fly deploy --remote-only`, `fly logs --app <app> -f`.

---

## Команды (Make)

Все команды проекта — через **Make**, не голый `uv run`. Список: `make help`.

| Действие | Команда |
|----------|---------|
| Установка зависимостей | `make install` |
| Запуск бота (webhook, prod) | `make run` |
| Запуск tgbot (polling, dev) | `make run-polling` |
| Запуск maxbot (polling, dev) | `make run-maxbot` |
| Docker (поднять Postgres/Redis) | `make docker-up` |
| Миграции (применить) | `make db-upgrade` |
| Миграции (создать) | `make db-revision` |
| Тесты (unit + integration) | `make test` |
| Unit-тесты | `make test-unit` |
| Integration-тесты | `make test-integration` |
| Линтинг + rules-check + тесты | `make check` |
| Линтинг | `make lint` / `make lint-fix` |
| Typecheck | `make typecheck` |

---

## Архитектурные принципы

> Канон (слои, DI, SQLAlchemy, async, Decimal, init, инъекции, ACL, миграции, именование) - в `~/Desktop/home/.claude/rules/python-standards.md` (грузится по `paths: **/*.py`). Диалоги/тесты/мультиплатформенность - соответствующие root-правила.
