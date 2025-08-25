.PHONY: help install install-dev test test-watch test-coverage test-unit test-integration lint format format-check clean db-reset setup setup-dev run monitor check

# Default target
help:
	@echo "Available commands:"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  test           - Run all tests"
	@echo "  test-watch     - Run tests with short traceback"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  lint           - Run flake8 linting"
	@echo "  format         - Format code with black"
	@echo "  format-check   - Check code formatting"
	@echo "  clean          - Clean Python cache files"
	@echo "  db-reset       - Remove database file"
	@echo "  setup          - Setup project (env + install)"
	@echo "  setup-dev      - Setup project for development"
	@echo "  run            - Run ZappiMon"
	@echo "  monitor        - Run ZappiMon (alias for run)"
	@echo "  check          - Check if ZappiMon module loads"

install:
	pip3 install -r requirements.txt

install-dev:
	pip3 install -r requirements.txt
	pip3 install -r requirements-dev.txt

test:
	python3 -m pytest test_zappimon.py -v

test-watch:
	python3 -m pytest test_zappimon.py -v --tb=short

test-coverage:
	python3 -m pytest test_zappimon.py --cov=ZappiMon --cov=database --cov-report=html --cov-report=term

test-unit:
	python3 -m pytest test_zappimon.py::TestZappiMon -v

test-integration:
	python3 -m pytest test_zappimon.py::TestZappiMonIntegration -v

lint:
	python3 -m flake8 ZappiMon.py database.py test_zappimon.py

format:
	python3 -m black ZappiMon.py database.py test_zappimon.py

format-check:
	python3 -m black --check ZappiMon.py database.py test_zappimon.py

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +

db-reset:
	rm -f zappimon.db

setup:
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		touch .env; \
		echo "Please edit .env with your credentials"; \
	fi
	pip3 install -r requirements.txt

setup-dev:
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		touch .env; \
		echo "Please edit .env with your credentials"; \
	fi
	pip3 install -r requirements.txt
	pip3 install -r requirements-dev.txt

run:
	python3 ZappiMon.py

monitor: run

check:
	python3 -c "import ZappiMon; print('ZappiMon module loaded successfully')"
