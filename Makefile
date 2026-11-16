.PHONY: dev check test build release-check

dev:
	uv sync --locked

check:
	uv run --locked mypy
	uv run --locked ty check src tests

test:
	uv run --locked pytest

build:
	uv build --no-sources

release-check:
	uv run --locked python scripts/release_check.py
