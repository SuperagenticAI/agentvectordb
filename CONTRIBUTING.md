# Contributing to AgentVectorDB

👍 First off, thanks for taking the time to contribute! 🎉

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project and everyone participating in it are governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Development Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/your-username/agentvectordb.git
cd agentvectordb
```

3. Set up your development environment:
```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## Development Process

1. Create a new branch for your feature/fix:
```bash
git checkout -b feature-name
```

2. Make your changes and ensure they follow our coding standards:
```bash
# Run linter
ruff check .

# Run tests
pytest
```

3. Commit your changes using conventional commits:
```bash
git commit -m "feat: add new feature"
# or
git commit -m "fix: resolve bug issue"
```

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the documentation if you're adding/changing functionality
3. Add tests for any new features
4. Ensure the test suite passes
5. Make sure your code follows our coding standards
6. Update the CHANGELOG.md following the Keep a Changelog format

## Coding Standards

We use Ruff for linting and formatting. Our code follows these principles:

- Follow PEP 8 style guide
- Maximum line length is 120 characters
- Use type hints for function arguments and return values
- Write docstrings for all public methods and classes
- Keep functions focused and concise

## Testing Guidelines

- Write unit tests for all new features
- Maintain test coverage above 80%
- Use pytest fixtures for reusable test components
- Name tests descriptively following `test_<what>_<expected>` pattern

Example test:
```python
def test_collection_creation_succeeds():
    store = AgentVectorDBStore(db_path="./test_db")
    collection = store.get_or_create_collection("test")
    assert collection is not None
```

## Documentation

- Update docstrings for any new/modified code
- Follow Google style docstrings
- Include code examples in docstrings
- Update the docs/ folder for any new features
- Add examples to the examples/ folder if applicable

Example docstring:
```python
def add_memory(self, content: str, importance: float) -> str:
    """Adds a new memory to the collection.

    Args:
        content (str): The content of the memory
        importance (float): Importance score between 0 and 1

    Returns:
        str: ID of the created memory

    Examples:
        >>> collection.add_memory("User query about vectors", 0.8)
        'mem_123456'
    """
```

## Release Process

1. Update version in pyproject.toml and setup.py
2. Update CHANGELOG.md
3. Create a new release on GitHub
4. GitHub Actions will automatically publish to PyPI

## Getting Help

- Open an issue for bugs or feature requests
- Join our [Discord/Slack] community
- Check our [FAQ](docs/faq.md)

## License

By contributing to AgentVectorDB, you agree that your contributions will be licensed under its Apache License 2.0.