# Concierge Bot — инструкции для Claude Code

## Rules structure (Claude Code)

Каноничные правила проекта - нативные Claude Code файлы в `.claude/rules/*.md`, каждый с `paths:` фронтматтером (не `globs:`) для path-scoped активации. Общий канон для всех ботов - в корневом `~/Desktop/home/.claude/rules/python-standards.md` (`paths: **/*.py`).

Добавить правило: создать `.md` напрямую в `.claude/rules/` с `paths:` и `description:` - симлинки не нужны. Не дублировать в этот CLAUDE.md.

Правило на новый path-паттерн: отредактировать `paths:` в нужном `.claude/rules/<file>.md` напрямую.

Общее для всех ботов вынесено в `~/Desktop/home/.claude/rules/` (python-standards, dialogs, config-pydantic, testing, multi-platform) - грузится автоматически по `paths:`.

---

## Critical (действует и в cloud-хотфиксах)

Полный канон - в `~/Desktop/home/.claude/rules/python-standards.md` (только локально, через tree-walk). Этот минимум продублирован прямо здесь, т.к. cloud/web-сессии клонируют только этот репо и home-правил не видят. Damage-class инварианты - необратимый/тихий урон в проде:

- Деньги -> `Decimal`, не `float`; БД `Numeric`. (IEEE754 -> биллинг-расхождения)
- SQL/HTML/shell/URL строки - не через f-string/`.format`/`%`: SQL параметризован, HTML экранирован. (инъекции)
- Stateless: глобалки под бизнес-данные / bg-таски из хендлера / состояние не в БД-Redis - запрещены. (Fly: рестарты + мульти-инстанс -> тихая потеря данных)
- Миграции: `DROP COLUMN`/`DROP TABLE` только с явным подтверждением и отдельной миграцией; проверить `down_revision`. (необратимо)
- Юзеру не показывать `str(exception)`/traceback - короткое сообщение, детали в логи. (утечка внутренностей)

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

**Fly.io приложения:**
- `bali-concierge` — бот (sin)
- `bali-concierge-db` — PostgreSQL кластер (sin)

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
│   ├── conftest.py           # cp metrika-bot/tests/conftest.py → правим
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/
│   ├── run_tests.sh          # cp metrika-bot/scripts/run_tests.sh → правим
│   ├── setup_dev.sh          # cp → правим
│   └── init_userbot.py       # cp metrika-bot userbot init → правим
├── sessions/                 # userbot сессии (gitignored)
├── .github/workflows/
│   └── fly-deploy.yml
├── Dockerfile
├── fly.toml
├── pyproject.toml            # cp metrika-bot/pyproject.toml → убрать лишние deps
├── alembic.ini               # cp metrika-bot/alembic.ini → правим пути
├── pytest.ini                # cp metrika-bot/pytest.ini → правим
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
# Установка
uv sync
uv sync --extra test
uv sync --extra lint

# Запуск
uv run python -m concierge_bot
uv run pytest tests/unit
uv run alembic upgrade head

# НЕ использовать pip напрямую
```

---

## Деплой

```bash
# Задеплоить бота
fly deploy --remote-only

# Миграции в продакшне
fly ssh console --app bali-concierge -C "alembic upgrade head"

# Логи
fly logs --app bali-concierge -f

# Подключиться к БД
fly pg connect --app bali-concierge-db --database concierge_bot
```

---

## Команды разработки

```bash
uv run python -m bali_concierge          # запуск бота
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
./scripts/run_tests.sh unit
./scripts/run_tests.sh integration
./scripts/run_tests.sh coverage

# Userbot (для e2e тестов)
uv run python -m tests.e2e.init_userbot  # создать сессию один раз
uv run pytest tests/e2e/ -x -v -m e2e

# E2E framework sync (из metrika-bot subtree)
make e2e-framework-sync
```

---

## Архитектурные принципы

> Канон (слои, DI, SQLAlchemy, async, Decimal, init, инъекции, ACL, миграции, именование) - в `~/Desktop/home/.claude/rules/python-standards.md` (грузится по `paths: **/*.py`). Диалоги/тесты/мультиплатформенность - соответствующие root-правила.
