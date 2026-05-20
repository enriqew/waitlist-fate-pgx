.PHONY: install install-dev lint test test-cov ingest dbt-run dbt-test clean

PYTHON := python
PIP    := pip

# ── Setup ──────────────────────────────────────────────────────────────────────

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev,dbt]"

# ── Quality ────────────────────────────────────────────────────────────────────

lint:
	ruff check src/ ingest/ tests/
	mypy src/ ingest/

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing

# ── Pipeline ───────────────────────────────────────────────────────────────────

ingest-waitlist:
	$(PYTHON) -m ingest.waitlist_artifacts

ingest-pgx:
	$(PYTHON) -m ingest.pgx_artifacts

ingest: ingest-waitlist ingest-pgx

# ── dbt ────────────────────────────────────────────────────────────────────────

dbt-run:
	cd dbt_project && dbt run

dbt-test:
	cd dbt_project && dbt test

dbt-docs:
	cd dbt_project && dbt docs generate && dbt docs serve

# ── Export ─────────────────────────────────────────────────────────────────────

export:
	$(PYTHON) -m src.waitlist_fate_pgx.export

# ── Cleanup ────────────────────────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache dist build *.egg-info
