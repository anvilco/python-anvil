PACKAGE := python_anvil

.PHONY: all
all: install

.PHONY: install
install: ## Install the package and its dev dependencies into .venv
	poetry install --all-extras

.PHONY: format
format: install ## Format the code and fix what the linter can
	poetry run ruff format .
	poetry run ruff check --fix .

.PHONY: lint
lint: install ## Check formatting, lint, and type-check
	poetry run ruff format --check .
	poetry run ruff check .
	poetry run mypy

.PHONY: test
test: install ## Run the unit tests with coverage
	poetry run pytest --cov --cov-report=term-missing:skip-covered

.PHONY: ci
ci: lint test ## Everything CI runs

.PHONY: test-client
test-client: install ## Run every method against a real environment (staging by default)
	poetry run python test-client.py

.PHONY: update-schema
update-schema: install ## Refresh schema/ from the published @anvilco/types and the API's OpenAPI spec
	poetry run python dev/fetch_schema.py

.PHONY: generate
generate: install ## Regenerate python_anvil/types from schema/
	poetry run python dev/generate_types.py

.PHONY: check-generated
check-generated: generate ## Fail if python_anvil/types is out of date with schema/
	git diff --exit-code -- python_anvil/types

.PHONY: build
build: install ## Build the sdist and wheel into dist/
	rm -rf dist
	poetry build

.PHONY: clean
clean: ## Delete generated and temporary files
	rm -rf dist .cache .coverage htmlcov
	find $(PACKAGE) tests -name '__pycache__' -exec rm -rf {} +

.PHONY: help
help:
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-10s %s\n", $$1, $$2}'
