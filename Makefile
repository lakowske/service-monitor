# Makefile for clean-python template
# This provides convenient shortcuts for common development tasks

SHELL := /bin/bash
PYTHON := python3
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help install test lint format type-check docs clean all pre-commit
.PHONY: install-service uninstall-service service-status service-logs restart-service start-service stop-service

# Service configuration
SERVICE_NAME := service-monitor
SERVICE_FILE := $(SERVICE_NAME).service
SYSTEMD_USER_DIR := $(HOME)/.config/systemd/user
PROJECT_DIR := $(shell pwd)
USER := $(shell whoami)
GROUP := $(shell id -gn)

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  help         - Show this help message"
	@echo "  install      - Install development dependencies using uv"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with ruff"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  docs         - Build documentation"
	@echo "  clean        - Clean build artifacts"
	@echo "  pre-commit   - Run all pre-commit checks"
	@echo "  all          - Run all checks (lint, format, type-check, test)"
	@echo ""
	@echo "Service Management:"
	@echo "  install-service   - Install and enable systemd service"
	@echo "  uninstall-service - Stop and remove systemd service"
	@echo "  start-service     - Start the service"
	@echo "  stop-service      - Stop the service"
	@echo "  restart-service   - Restart the service"
	@echo "  service-status    - Show service status"
	@echo "  service-logs      - View service logs"

# Create virtual environment using uv
$(VENV_DIR):
	@echo -e "$(YELLOW)Creating virtual environment with uv...$(NC)"
	uv venv $(VENV_DIR)
	@echo -e "$(GREEN)✓ Virtual environment created at $(VENV_DIR)$(NC)"

# Install dependencies using uv
install: $(VENV_DIR)
	@echo "Installing development dependencies with uv..."
	uv pip install --python $(VENV_PYTHON) -e ".[dev]"

# Run tests with coverage
test:
	pytest --cov=src --cov-report=term-missing --cov-fail-under=80 --cov-report=html

# Run linting
lint:
	ruff check .

# Format code
format:
	ruff format .

# Run type checking
type-check:
	mypy src

# Build documentation
docs:
	@if [ -f "mkdocs.yml" ]; then \
		mkdocs build; \
	else \
		echo "No mkdocs.yml found. Run 'mkdocs new .' to initialize docs."; \
	fi

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf site/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run pre-commit checks
pre-commit:
	pre-commit run --all-files

# Run all checks
all: lint format type-check test
	@echo "All checks passed!"

# Systemd Service Management Targets

# Install and enable the systemd service
install-service: $(VENV_DIR)
	@echo -e "$(YELLOW)Installing systemd service...$(NC)"
	@mkdir -p $(SYSTEMD_USER_DIR)
	@sed -e 's|%PROJECT_DIR%|$(PROJECT_DIR)|g' \
	     $(SERVICE_FILE) > $(SYSTEMD_USER_DIR)/$(SERVICE_FILE)
	@chmod 644 $(SYSTEMD_USER_DIR)/$(SERVICE_FILE)
	@systemctl --user daemon-reload
	@systemctl --user enable $(SERVICE_NAME).service
	@echo -e "$(GREEN)✓ Service installed and enabled$(NC)"
	@echo -e "$(YELLOW)To start the service, run: make start-service$(NC)"
	@echo -e "$(YELLOW)To enable automatic start on boot, run: loginctl enable-linger $(USER)$(NC)"

# Uninstall and remove the systemd service
uninstall-service:
	@echo -e "$(YELLOW)Uninstalling systemd service...$(NC)"
	@systemctl --user stop $(SERVICE_NAME).service 2>/dev/null || true
	@systemctl --user disable $(SERVICE_NAME).service 2>/dev/null || true
	@rm -f $(SYSTEMD_USER_DIR)/$(SERVICE_FILE)
	@systemctl --user daemon-reload
	@echo -e "$(GREEN)✓ Service uninstalled$(NC)"

# Start the service
start-service:
	@echo -e "$(YELLOW)Starting service...$(NC)"
	@systemctl --user start $(SERVICE_NAME).service
	@echo -e "$(GREEN)✓ Service started$(NC)"
	@systemctl --user status $(SERVICE_NAME).service --no-pager

# Stop the service
stop-service:
	@echo -e "$(YELLOW)Stopping service...$(NC)"
	@systemctl --user stop $(SERVICE_NAME).service
	@echo -e "$(GREEN)✓ Service stopped$(NC)"

# Restart the service
restart-service:
	@echo -e "$(YELLOW)Restarting service...$(NC)"
	@systemctl --user restart $(SERVICE_NAME).service
	@echo -e "$(GREEN)✓ Service restarted$(NC)"
	@systemctl --user status $(SERVICE_NAME).service --no-pager

# Show service status
service-status:
	@systemctl --user status $(SERVICE_NAME).service

# View service logs
service-logs:
	@journalctl --user -u $(SERVICE_NAME).service -f
