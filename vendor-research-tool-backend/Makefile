PYTHON ?= python3

.PHONY: lint format format-check typecheck test check security

lint:
	$(PYTHON) -m ruff check app/ tests/
format:
	$(PYTHON) -m ruff format app/ tests/
format-check:
	$(PYTHON) -m ruff format --check app/ tests/
typecheck:
	$(PYTHON) -m pyright app/
test:
	$(PYTHON) -m pytest tests/
check: lint format-check typecheck test
	@echo "All quality gates passed."
security:
	pip-audit
