# Contributing to SQLAlchemy-ViewORM

Thank you for your interest in contributing to SQLAlchemy-ViewORM! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our code of conduct: be respectful, considerate, and collaborative.

## How to Contribute

### Reporting Bugs

If you find a bug, please submit an issue with:

1. A clear and descriptive title
2. Steps to reproduce the bug
3. Expected behavior
4. Actual behavior
5. Environment details (OS, Python version, SQLAlchemy version, etc.)
6. Any additional context that might help

### Suggesting Enhancements

We welcome suggestions for enhancements! Please submit an issue with:

1. A clear and descriptive title
2. A detailed description of the proposed enhancement
3. Examples of how the enhancement would be used
4. Any relevant context or background

### Pull Requests

We actively welcome pull requests. Here's how to submit one:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

1. Clone your fork of the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Testing

We use pytest for testing. Run the tests with:

```bash
pytest
```

For coverage reports:

```bash
pytest --cov=sqlalchemy_view_orm
```

## Code Style

We follow these coding standards:

- Black for code formatting
- isort for import sorting
- mypy for type checking
- flake8 for linting

You can run these tools manually or use pre-commit hooks.

## Documentation

When adding new features, please update the relevant documentation:

- Update docstrings for public classes and methods
- Update README.md if necessary
- Add examples if appropriate

## Versioning

We use [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH).

## Release Process

1. Update version in `sqlalchemy_view_orm/__init__.py`
2. Update CHANGELOG.md
3. Create a new GitHub release with the version number

## Getting Help

If you need help with the contribution process, feel free to open an issue with your question.

## License

By contributing to SQLAlchemy-ViewORM, you agree that your contributions will be licensed under the project's MIT License.
