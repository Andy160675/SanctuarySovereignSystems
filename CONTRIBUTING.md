# Contributing to SanctuarySovereignSystems

Thank you for your interest in contributing to Governance For AI!

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run quality checks:
   ```bash
   ruff check .
   ruff format --check .
   mypy .
   pytest
   ```
4. Commit your changes with a clear message
5. Push to your fork and open a Pull Request

## Code Standards

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use type annotations for all function signatures
- Write docstrings for public modules, classes, and functions
- Maintain test coverage above 80%

## Pull Request Guidelines

- Keep PRs focused on a single change
- Include tests for new functionality
- Update documentation if needed
- Ensure all CI checks pass before requesting review

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- Include steps to reproduce for bug reports
- Check existing issues before creating duplicates

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
