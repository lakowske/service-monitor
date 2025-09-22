# Clean Python Template

A modern Python project template with pre-configured best practices, designed to help you start new Python projects quickly and efficiently.

## 🚀 Features

- **Modern Python Packaging**: Uses `pyproject.toml` for all project configuration
- **Ruff**: Lightning-fast Python linter and formatter (replaces Black, Flake8, isort, and Bandit)
- **Pydantic**: Data validation and settings management
- **Dataclasses**: Simple data structures with type hints
- **Pre-commit Hooks**: Automated code quality checks before every commit
- **Testing**: Pytest with coverage reporting (minimum 80% required)
- **Type Checking**: MyPy for static type analysis
- **Documentation**: MkDocs with Material theme
- **UV Support**: Modern Python package manager
- **Makefile**: Convenient development commands
- **VS Code Integration**: Pre-configured settings for optimal development experience

## 🎯 Quick Start

### 1. Use the Template

Clone this repository and run the setup script:

```bash
git clone https://github.com/lakowske/clean-python.git
cd clean-python
python setup_new_project.py
```

### 2. Set Up Development Environment

```bash
cd ../your-new-project
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make install  # or pip install -e ".[dev]"
```

### 3. Install Pre-commit Hooks

```bash
pre-commit install
```

### 4. Start Coding!

Your project is now ready with all the modern Python development tools configured!

## 📚 Documentation

- [Getting Started](getting-started.md) - Detailed setup instructions
- [Development](development.md) - Development workflow and tools
- [Examples](examples.md) - Code examples and patterns
- [API Reference](api.md) - Complete API documentation

## 🛠️ Built With

- [Ruff](https://github.com/astral-sh/ruff) - An extremely fast Python linter and formatter
- [Pydantic](https://pydantic.dev/) - Data validation using Python type hints
- [Pytest](https://pytest.org) - The pytest framework
- [Pre-commit](https://pre-commit.com) - A framework for managing git hooks
- [MkDocs](https://www.mkdocs.org/) - Project documentation with Markdown
- [UV](https://github.com/astral-sh/uv) - An extremely fast Python package installer and resolver

## 📄 License

This template is released under the MIT License. Your generated projects can use any license you prefer.
