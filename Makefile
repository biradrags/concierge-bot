.PHONY: help install clean
.PHONY: run run-polling run-maxbot
.PHONY: docker-up docker-down docker-logs
.PHONY: db-upgrade db-downgrade db-revision db-current
.PHONY: test test-unit test-integration check lint lint-fix typecheck

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Setup

install: ## Install dependencies (dev + test + lint)
	uv sync --extra test --extra lint

clean: ## Remove caches and build artifacts
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

##@ Run

run: ## Webhook mode (production entry)
	uv run python -m concierge_bot

run-polling: ## Telegram polling (development)
	uv run python -m concierge_bot.tgbot

run-maxbot: ## VK Max polling (development)
	uv run python -m concierge_bot.maxbot

##@ Docker

docker-up: ## Start postgres + redis
	docker compose up -d

docker-down: ## Stop docker services
	docker compose down

docker-logs: ## Follow docker logs
	docker compose logs -f

##@ Database

db-upgrade: ## Alembic upgrade head
	uv run alembic upgrade head

db-downgrade: ## Alembic downgrade one revision
	uv run alembic downgrade -1

db-revision: ## New autogenerate migration
	@read -p "Migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

db-current: ## Current Alembic revision
	uv run alembic current

##@ Tests & quality

test: ## Fast tests (excludes integration; use test-integration for Postgres)
	uv run pytest tests -v

test-unit: ## Unit tests only
	uv run pytest tests/unit -v

test-integration: ## Integration tests only (needs Postgres, see docker-up)
	uv run pytest tests -m integration -v

lint: ## Ruff check
	uv run ruff check .

lint-fix: ## Ruff check with auto-fix
	uv run ruff check --fix .

typecheck: ## Mypy
	uv run mypy concierge_bot

check: ## Lint + tests (no typecheck until codebase stabilizes)
	uv run ruff check .
	uv run pytest tests -v
