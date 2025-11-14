.PHONY: help install install-min dev lint format test clean build publish serve serve-dev sample info

# Default target
help:
	@echo "FivcAdvisor - Available Make Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install      - Install with dev dependencies (default)"
	@echo "  install-min  - Install minimal runtime dependencies only"
	@echo "  dev          - Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  lint         - Run code linting with ruff"
	@echo "  format       - Format code with ruff"
	@echo "  test         - Run tests with pytest"
	@echo "  clean        - Clean temporary files and caches"
	@echo ""
	@echo "Distribution:"
	@echo "  build        - Build package distributions (wheel and source)"
	@echo "  publish      - Publish package to PyPI"
	@echo ""
	@echo "Running:"
	@echo "  serve        - Start Streamlit web interface (production)"
	@echo "  serve-dev    - Start Streamlit web interface (development)"
	@echo "  sample       - Run sample configuration (dry-run)"
	@echo "  info         - Show system information"
	@echo ""

# Installation targets
install:
	@echo "Installing FivcPlayground with development dependencies..."
	uv sync --extra dev

install-min:
	@echo "Installing FivcPlayground with minimal dependencies..."
	uv sync

dev:
	@echo "Installing development dependencies..."
	uv sync --extra dev

# Development targets
lint: dev
	@echo "Running code linting..."
	uv run ruff check src tests

format: dev
	@echo "Formatting code..."
	uv run ruff format src tests

test: dev
	@echo "Running tests..."
	uv run python -m pytest -q

clean:
	@echo "Cleaning temporary files..."
	uv run fivcplayground clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Distribution targets
build: clean dev
	@echo "Building package distributions..."
	@echo "Removing existing build artifacts..."
	rm -rf dist/ build/ 2>/dev/null || true
	@echo "Building wheel and source distributions..."
	uv run python -m build
	@echo "Build complete! Distributions available in dist/"

publish: build
	@echo "Publishing package to PyPI..."
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist/)" ]; then \
		echo "Error: No distributions found in dist/ directory"; \
		echo "Please run 'make build' first"; \
		exit 1; \
	fi
	uv run python -m twine upload dist/*
	@echo "Package published successfully!"

# Web interface targets
serve:
	@echo "Starting FivcPlayground web interface..."
	@echo "Access at: http://localhost:8501"
	@echo "Press Ctrl+C to stop"
	uv run fivcplayground web

serve-dev:
	@echo "Starting FivcAdvisor web interface (development mode)..."
	@echo "Access at: http://localhost:8501"
	@echo "Press Ctrl+C to stop"
	uv run streamlit run src/fivcadvisor/app/__init__.py --server.port 8501

# Utility targets
sample:
	@echo "Running sample configuration..."
	uv run fivcadvisor --config configs/sample.yaml --dry-run

info:
	@echo "Showing system information..."
	uv run fivcadvisor info
