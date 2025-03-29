# Contributing to MyCoder-Py

We welcome contributions to MyCoder-Py! Whether it's bug fixes, new features, documentation improvements, or any other enhancement, we appreciate your help in making this project better.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/mycoder-py.git
   cd mycoder-py
   ```
3. **Set up the development environment**:
   ```bash
   # With Poetry (recommended)
   poetry install --with dev
   
   # Or with pip
   pip install -e ".[dev]"
   ```
4. **Create a new branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

You can run these tools on your code before submitting:

```bash
# Format code
poetry run black src tests

# Run linter
poetry run ruff check src tests

# Run type checker
poetry run mypy src
```

### Running Tests

We use pytest for testing:

```bash
# Run all tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=mycoder
```

### Documentation

When adding new features, please update the relevant documentation:

- Add docstrings to new functions, classes, and methods
- Update the documentation files in the `docs/` directory as needed
- Add examples if appropriate

## Pull Request Process

1. **Ensure your code passes all checks**:
   - All tests pass
   - Code is formatted with Black
   - No linting errors from Ruff
   - No type errors from MyPy

2. **Update documentation** if necessary

3. **Write a clear pull request description**:
   - Explain what your changes do
   - Reference any related issues
   - Note any breaking changes

4. **Submit your pull request** for review

## Adding New Features

### Adding a New Tool

1. Create a new file in `mycoder/agent/tools/` or add to an existing file
2. Define a Pydantic model for your tool's arguments
3. Implement the Tool class by extending the base Tool class
4. Add appropriate error handling
5. Add your tool to the registry in `__init__.py`
6. Add tests for your tool

### Adding a New LLM Provider

1. Create a new file in `mycoder/agent/llm/` (e.g., `anthropic.py`)
2. Implement the provider by extending the LLMProvider abstract class
3. Create a configuration class if needed
4. Add factory functions for easy instantiation
5. Update the `__init__.py` file to export your provider
6. Add tests for your provider

## Code of Conduct

### Our Standards

- **Be respectful** of others and their time
- **Focus on what is best** for the community
- **Show empathy** towards other community members

### Our Responsibilities

Maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

## License

By contributing to MyCoder-Py, you agree that your contributions will be licensed under the project's MIT License. 