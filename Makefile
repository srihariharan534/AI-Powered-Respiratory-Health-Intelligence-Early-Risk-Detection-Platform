.PHONY: help setup dev test lint format clean backtest evaluate benchmark demo reset health-check db-up db-down db-migrate db-status db-reset

help:
	@echo "NEXUS Emergency Decision Intelligence Platform"
	@echo "Available commands:"
	@echo "  make setup        - Install development dependencies"
	@echo "  make dev          - Launch development services (Configured in Phase 02/12)"
	@echo "  make test         - Execute repository test suite"
	@echo "  make db-up        - Start PostgreSQL + PostGIS container and wait for healthy"
	@echo "  make db-down      - Stop PostgreSQL + PostGIS container"
	@echo "  make db-migrate   - Apply pending database migrations via Alembic"
	@echo "  make db-status    - Verify database connectivity and PostGIS status"
	@echo "  make db-reset     - [DESTRUCTIVE] Reset local database volume and re-run migrations"
	@echo "  make lint         - Run static code analysis and linting"
	@echo "  make format       - Automatically format codebase"
	@echo "  make health-check - Validate developer environment & toolchains"
	@echo "  make backtest     - Run historical flood backtesting (Configured in Phase 28)"
	@echo "  make evaluate     - Compute evaluation metrics (Configured in Phase 29)"
	@echo "  make benchmark    - Run performance benchmarks (Configured in Phase 30)"
	@echo "  make demo         - Launch Judge Mode scenario (Configured in Phase 14/31)"
	@echo "  make clean        - Clean temporary cache and build artifacts"
	@echo "  make reset        - Reset local digital twin state (Configured in Phase 09)"

setup:
	@echo "==> Setting up NEXUS environment..."
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

dev:
	@echo "==> [Phase 02] Running Docker Compose development stack..."
	docker compose up --no-build

db-up:
	@echo "==> Launching PostGIS database container..."
	docker compose up -d db
	@echo "==> Waiting for database to become healthy..."
	@docker compose ps db

db-down:
	@echo "==> Stopping PostGIS database container..."
	docker compose stop db

db-migrate:
	@echo "==> Running database migrations..."
	alembic upgrade head

db-status:
	@echo "==> Checking database connection and PostGIS version..."
	python -c "from services.api.app.database import get_engine; from sqlalchemy import text; engine=get_engine(); conn=engine.connect(); print('PostgreSQL Ready. PostGIS Version:', conn.execute(text('SELECT PostGIS_Version();')).scalar()); conn.close()"

db-reset:
	@echo "==> [CAUTION] Resetting development database and volume..."
	docker compose down -v
	docker compose up -d db
	@echo "==> Database re-created. Applying migrations..."
	alembic upgrade head

test:
	@echo "==> Running unit test suite..."
	pytest tests/unit/ tests/test_constitution.py -v

health-check:
	@echo "==> Checking development environment health..."
	python scripts/health_check/check_environment.py

lint:
	@echo "==> Running linters..."
	ruff check .

format:
	@echo "==> Formatting code..."
	ruff format .

backtest:
	@echo "==> [Phase Notice] Historical backtesting engine will be implemented in Phase 28."

evaluate:
	@echo "==> [Phase Notice] Automated evaluation pipeline will be implemented in Phase 29."

benchmark:
	@echo "==> [Phase Notice] Latency benchmarks will be implemented in Phase 30."

demo:
	@echo "==> [Phase Notice] Deterministic Judge Mode demonstration will be implemented in Phase 14 & 31."

clean:
	@echo "==> Cleaning cache artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

reset:
	@echo "==> [Phase Notice] Digital Twin state reset will be implemented in Phase 09."
