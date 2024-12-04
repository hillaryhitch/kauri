# Makefile for Kazuri development

.PHONY: install test clean lint format

# Install development dependencies
install:
	pip install -e ".[dev]"
	pip install -r requirements.txt

# Run tests
test:
	pytest tests/ -v

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type d -name "dist" -exec rm -r {} +
	find . -type d -name "build" -exec rm -r {} +

# Run linting
lint:
	flake8 kazuri tests
	mypy kazuri tests
	black --check kazuri tests
	isort --check-only kazuri tests

# Format code
format:
	black kazuri tests
	isort kazuri tests

# Build package
build: clean
	python setup.py sdist bdist_wheel

# Install pre-commit hooks
pre-commit:
	pre-commit install

# Run development server (if needed)
serve:
	uvicorn kazuri.main:app --reload

# Create documentation
docs:
	mkdocs build

# Serve documentation locally
docs-serve:
	mkdocs serve

# Help target
help:
	@echo "Available targets:"
	@echo "  install     - Install development dependencies"
	@echo "  test        - Run tests"
	@echo "  clean       - Clean up Python cache files"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code"
	@echo "  build       - Build package"
	@echo "  pre-commit  - Install pre-commit hooks"
	@echo "  serve       - Run development server"
	@echo "  docs        - Build documentation"
	@echo "  docs-serve  - Serve documentation locally"
