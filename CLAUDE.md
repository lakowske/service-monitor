# Clean Python Project Template

## Project Purpose

This is a template for creating clean, professional Python projects that incorporate industry best practices from the start. It serves as a foundation for new Python projects with all the essential development tools and quality assurance measures pre-configured.

For detailed usage instructions and features, see [README.md](README.md).

## Clean Code Practices Implemented

### Code Quality & Standards

- **Ruff** - Fast, all-in-one Python linter and formatter (replaces Black, Flake8, isort, and Bandit)
  - Automatic code formatting with 120 character line length
  - Comprehensive linting with Google docstring conventions
  - Import sorting and security checks included
- **mdformat** - Markdown formatting with GitHub Flavored Markdown support
- **Pre-commit hooks** - Automated quality checks before every commit

### Testing & Coverage

- **Pytest** - Modern testing framework with proper project structure
- **Coverage reporting** - Minimum 80% code coverage required
- **HTML coverage reports** - Generated in `htmlcov/` directory
- **Integration testing** - Structured test organization

### Git Workflow

- **Pre-commit configuration** - Ensures code quality on every commit
- **Automated checks** for:
  - Trailing whitespace removal
  - End-of-file fixing
  - YAML validation
  - Large file detection
  - Code formatting and linting (Ruff)
  - Markdown formatting (mdformat with GFM support)
  - Test coverage (Pytest with 80% minimum)

## Project Structure

```text
clean-python/
├── actions/          # Project build and automation scripts
├── tests/           # Test suite with pytest configuration
├── build/           # Build artifacts (auto-generated)
├── htmlcov/         # HTML coverage reports
├── .pre-commit-config.yaml  # Pre-commit hook configuration
└── setup.cfg        # Project metadata and configuration
```

## Development Commands

- `pytest --cov=. --cov-report=term-missing --cov-fail-under=80 --cov-report=html` - Run tests with coverage
- `ruff format .` - Format code
- `ruff check .` - Run linting
- `ruff check --fix .` - Run linting with auto-fixes
- `pre-commit install` - Install pre-commit hooks
- `pre-commit run --all-files` - Run all pre-commit checks

## Logging Standards

All code should implement comprehensive logging with the following requirements:

- **Severity levels** - Use appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **File location** - Include `__name__` or explicit file path in logger configuration
- **Line numbers** - Use `%(lineno)d` in formatter to capture line numbers
- **Operation context** - Log the operation being performed with descriptive messages
- **Variable tracking** - Include relevant variable names and their values in log messages

### Example Logging Configuration

```python
import logging

# Configure logger with comprehensive formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Example usage
def process_data(data_id, data_content):
    logger.info(f"Starting data processing - data_id: {data_id}, content_length: {len(data_content)}")
    try:
        # Process data
        result = transform_data(data_content)
        logger.debug(f"Data transformation successful - result_type: {type(result)}, result_size: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Data processing failed - data_id: {data_id}, error: {str(e)}", exc_info=True)
        raise
```

## Quality Gates

Every commit must pass:

1. Code formatting and linting (Ruff)
1. Markdown formatting (mdformat)
1. All tests passing
1. Minimum 80% code coverage
1. No trailing whitespace
1. Proper file endings
1. Valid YAML syntax

This template ensures that code quality, testing, and documentation standards are maintained throughout the development lifecycle.

## Quick Usage Examples for Claude

### Example 1: Create a new API project interactively

```bash
# Clone and enter the template
git clone https://github.com/lakowske/clean-python.git
cd clean-python

# Run setup interactively
python setup_new_project.py
# Enter when prompted:
# Project name: fastapi-todo-app
# Description: A REST API for managing todo items
# Author: John Smith
# Email: john.smith@example.com
# GitHub username: johnsmith
```

### Example 2: Create a CLI tool project with all arguments

```bash
# Clone template
git clone https://github.com/lakowske/clean-python.git
cd clean-python

# One-line setup with all arguments
python setup_new_project.py \
    --name python-file-organizer \
    --description "A CLI tool to organize files by type and date" \
    --author "Jane Developer" \
    --email "jane@dev.com" \
    --github "janedev" \
    -y
```

### Example 3: Create a data science project in a specific directory

```bash
# Clone template
git clone https://github.com/lakowske/clean-python.git
cd clean-python

# Create project in custom location
python setup_new_project.py \
    --name ml-sentiment-analysis \
    --description "Machine learning project for sentiment analysis" \
    --author "Data Scientist" \
    --email "ds@company.com" \
    --output-dir ~/projects/ml/sentiment-analysis
```

### After Project Creation

The new project will be created with:

- All configuration files updated with project information
- Python package renamed to match the project
- Fresh git repository initialized with first commit
- Ready for development with all tools pre-configured

Next steps in the new project:

```bash
cd ../my-new-project  # or cd to your custom output directory
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

Now you can start coding with all quality checks automated!
