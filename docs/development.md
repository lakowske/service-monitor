# Development Workflow

This guide covers the development workflow and tools available in your clean-python project.

## Available Commands

The project includes a Makefile with convenient shortcuts for common development tasks:

```bash
make help         # Show all available commands
make install      # Install development dependencies
make test         # Run tests with coverage
make lint         # Run linting checks
make format       # Format code with ruff
make type-check   # Run type checking with mypy
make docs         # Build documentation
make clean        # Clean build artifacts
make pre-commit   # Run all pre-commit checks
make all          # Run all checks (lint, format, type-check, test)
```

## Development Tools

### Ruff - Code Quality

Ruff is an extremely fast Python linter and formatter that replaces multiple tools:

```bash
# Format code
ruff format .

# Run linting
ruff check .

# Auto-fix issues
ruff check --fix .
```

Configuration is in `pyproject.toml` under `[tool.ruff]`.

### MyPy - Type Checking

MyPy is a static type checker for Python:

```bash
# Run type checking
mypy .

# Check specific files
mypy src/my_project/core.py
```

Configuration is in `pyproject.toml` under `[tool.mypy]`.

### Pytest - Testing

Pytest is configured with coverage reporting:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest -v
```

Configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`.

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

The hooks include:

- Trailing whitespace removal
- End-of-file fixing
- YAML validation
- Large file detection
- Ruff linting and formatting
- Type checking with MyPy
- Markdown formatting
- Test coverage validation

## Package Management

### Using UV (Recommended)

UV is a fast Python package manager:

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Add new dependency
uv add requests

# Add development dependency
uv add --dev pytest-mock

# Update dependencies
uv pip install --upgrade-package package-name
```

### Using pip

```bash
# Install dependencies
pip install -e ".[dev]"

# Add new dependency (manually edit pyproject.toml)
pip install -e ".[dev]"
```

## Code Examples

The template includes modern Python patterns:

### Pydantic Models

```python
from pydantic import BaseModel, Field, model_validator

class UserProfile(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    age: Optional[int] = Field(None, ge=0, le=120)

    @model_validator(mode='after')
    def validate_model(self) -> 'UserProfile':
        if any(char.isdigit() for char in self.name):
            raise ValueError('Name cannot contain numbers')
        self.name = self.name.strip().title()
        return self
```

### Dataclasses

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Union, Optional

@dataclass
class CalculationResult:
    operand_a: Union[int, float]
    operand_b: Union[int, float]
    operation: str
    result: Union[int, float]
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            'operand_a': self.operand_a,
            'operand_b': self.operand_b,
            'operation': self.operation,
            'result': self.result,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
```

## Testing Patterns

### Testing Pydantic Models

```python
import pytest
from pydantic import ValidationError

def test_user_profile_validation():
    # Test valid data
    profile = UserProfile(name="John Doe", email="john@example.com")
    assert profile.name == "John Doe"

    # Test validation error
    with pytest.raises(ValidationError):
        UserProfile(name="John123", email="john@example.com")
```

### Testing Dataclasses

```python
def test_calculation_result():
    result = CalculationResult(
        operand_a=10,
        operand_b=5,
        operation="subtraction",
        result=5
    )
    assert result.operand_a == 10
    assert result.to_dict()["operation"] == "subtraction"
```

## Documentation

### Building Documentation

```bash
# Build documentation
make docs

# Serve documentation locally
mkdocs serve

# Deploy to GitHub Pages
mkdocs gh-deploy
```

### Writing Documentation

Documentation is written in Markdown and built with MkDocs:

- `docs/index.md` - Main documentation page
- `docs/getting-started.md` - Getting started guide
- `docs/development.md` - Development workflow
- `docs/examples.md` - Code examples
- `docs/api.md` - API reference

## VS Code Integration

The template includes VS Code configuration:

- **Recommended extensions**: Ruff, Python, MyPy
- **Format on save**: Enabled
- **Integrated terminal**: Configured for Python development
- **Debugging**: Pre-configured for Python

## Logging Best Practices

The template includes comprehensive logging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Use in functions
def process_data(data):
    logger.info(f"Processing data - size: {len(data)}")
    try:
        # Process data
        result = transform(data)
        logger.debug(f"Processing complete - result_size: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Processing failed - error: {str(e)}", exc_info=True)
        raise
```

## Continuous Integration

The template is ready for CI/CD integration. Consider adding:

- GitHub Actions for automated testing
- Code coverage reporting
- Automated dependency updates
- Security scanning
- Automated releases

## Performance Tips

- Use UV for faster package management
- Enable `--parallel` for pytest on multi-core systems
- Use `ruff --fix` for automatic code fixes
- Configure pre-commit hooks to run only on changed files for speed
