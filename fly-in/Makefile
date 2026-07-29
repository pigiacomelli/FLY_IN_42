.PHONY: install run debug test clean lint lint-strict check

ARGS ?=

install:
	uv sync

run:
	uv run python -m fly_in $(ARGS)

debug:
	uv run python -m pdb -m fly_in $(ARGS)

test:
	uv run python -m pytest $(ARGS)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache
	rm -rf .pytest_cache

lint:
	uv run flake8 . --exclude=.venv
	uv run mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	uv run flake8 . --exclude=.venv
	uv run mypy . --strict

check: lint test