# service-monitor

A Python application for monitoring services and their health status

## Features

- Modern Python project structure
- Comprehensive testing with pytest and coverage reporting
- Code quality tools (Ruff for linting/formatting, MyPy for type checking)
- Pre-commit hooks for automated quality checks
- GitHub Actions CI/CD pipeline
- VS Code tasks integration

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Git

### Installation

1. Clone the repository:

```bash
git clone https://github.com/lakowske/service-monitor.git
cd service-monitor
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the project in development mode:

```bash
# Using Make (recommended)
make install

# Or using UV (fastest)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

4. Install pre-commit hooks:

```bash
pre-commit install
```

## Development

### Available Commands

```bash
# Using Make (recommended)
make help         # Show all available commands
make test         # Run tests with coverage
make lint         # Run linting
make format       # Format code
make type-check   # Run type checking
make docs         # Build documentation
make all          # Run all checks

# Or run tools directly
pytest --cov=. --cov-report=term-missing --cov-fail-under=80 --cov-report=html
ruff format .     # Format code
ruff check .      # Lint code
mypy .           # Run type checking
mkdocs serve     # Serve documentation locally
pre-commit run --all-files  # Run all checks
```

### VS Code Integration

This project includes VS Code tasks for common operations:

- `Ctrl+Shift+P` -> "Tasks: Run Task" to see all available tasks
- Install the "Task Explorer" extension for a better task management experience

## Project Structure

```
service-monitor/
├── src/service_monitor/     # Main package
├── tests/                          # Test suite
├── .github/workflows/              # GitHub Actions
├── .vscode/                        # VS Code configuration
├── pyproject.toml                  # Project configuration
└── README.md                       # This file
```

## Contributing

1. Fork the repository
1. Create a feature branch: `git checkout -b feature/amazing-feature`
1. Make your changes and run the quality checks
1. Commit your changes: `git commit -m 'Add amazing feature'`
1. Push to the branch: `git push origin feature/amazing-feature`
1. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Seth Lakowske - lakowske@gmail.com
