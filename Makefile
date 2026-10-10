.DEFAULT_GOAL := help

.PHONY: install run test lint format typecheck coverage clean help

install:
	cd backend && uv sync

run:
	cd backend && uv run uvicorn app.main:app --reload

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check .

format:
	cd backend && uv run ruff format .

typecheck:
	cd backend && uv run pyright

coverage:
	cd backend && uv run pytest --cov=app --cov-report=term-missing

clean:
	find . -type d \( -name "__pycache__" -o -name ".ruff_cache" -o -name ".pytest_cache" \) -prune -exec rm -rf {} +

help:
	@echo "make install       - Install dependencies"
	@echo "make run           - Run FastAPI server"
	@echo "make test          - Run tests"
	@echo "make lint          - Lint code"
	@echo "make format        - Format code"
	@echo "make coverage      - Run tests with coverage report"
	@echo "make clean         - Remove Python/tool caches"