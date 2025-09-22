# Getting Started

This guide will help you create a new Python project using the clean-python template.

## Prerequisites

- Python 3.9 or higher
- Git
- pip (or uv for faster package management)

## Creating a New Project

### Option 1: Interactive Setup (Recommended)

1. **Clone the template:**

   ```bash
   git clone https://github.com/lakowske/clean-python.git
   cd clean-python
   ```

1. **Run the setup script:**

   ```bash
   python setup_new_project.py
   ```

1. **Follow the prompts to enter:**

   - Project name (e.g., `my-awesome-project`)
   - Project description
   - Your name
   - Your email
   - GitHub username (optional)

### Option 2: Command Line Setup

Provide all information via command line arguments:

```bash
python setup_new_project.py \
    --name my-awesome-project \
    --description "A fantastic Python project" \
    --author "Jane Doe" \
    --email jane.doe@example.com \
    --github janedoe
```

### Option 3: Custom Directory Setup

Create the project in a specific location:

```bash
python setup_new_project.py \
    --name my-project \
    --output-dir ~/projects/my-new-project
```

## Development Environment Setup

After creating your project, navigate to the new directory and set up your development environment:

### Using Make (Recommended)

```bash
cd ../your-new-project
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make install
```

### Using pip directly

```bash
cd ../your-new-project
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Using uv (Fastest)

```bash
cd ../your-new-project
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

## Install Pre-commit Hooks

Pre-commit hooks ensure code quality on every commit:

```bash
pre-commit install
```

## Verify Installation

Run the tests to make sure everything is working:

```bash
make test
# or
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

## Project Structure

Your new project will have this structure:

```
my-project/
├── src/
│   └── my_project/          # Your package (renamed from clean_python)
│       ├── __init__.py
│       ├── core.py          # Example module with Pydantic and dataclasses
│       └── actions/         # Example subpackage
├── tests/                   # Test suite
│   ├── conftest.py
│   └── test_*.py
├── docs/                    # Documentation
├── .github/                 # GitHub templates
├── .vscode/                 # VS Code settings
├── .pre-commit-config.yaml  # Pre-commit hooks
├── pyproject.toml          # Project configuration
├── mkdocs.yml              # Documentation configuration
├── Makefile                # Development commands
├── .gitignore
└── README.md               # Your project's README
```

## Next Steps

1. **Start coding** - The template includes example code with Pydantic and dataclasses
1. **Write tests** - Add tests for your new functionality
1. **Update documentation** - Modify the docs to reflect your project
1. **Set up CI/CD** - Add GitHub Actions for automated testing
1. **Deploy** - Use the deployment tools of your choice

Congratulations! You now have a modern Python project with all the best practices configured.
