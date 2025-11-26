# Contributing to Sovereign System

Thank you for your interest in contributing to the Sovereign System governance framework.

## Code of Conduct

This project operates under a principle of **institutional integrity**. All contributions must:

1. Maintain the constitutional guarantees of V3
2. Pass existing test suites before merge
3. Be additive rather than breaking
4. Include appropriate test coverage

## How to Contribute

### Reporting Issues

1. Check existing issues first
2. Provide clear reproduction steps
3. Include relevant logs and chain state (sanitized)
4. Label appropriately: `bug`, `enhancement`, `security`

### Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest tests/`
5. Submit PR with clear description

### Commit Messages

Use clear, descriptive commit messages:

```
[Component] Brief description

- Detailed change 1
- Detailed change 2

Closes #123
```

### Code Style

- Python: Follow PEP 8
- Use type hints where practical
- Document public functions with docstrings
- Keep functions focused and testable

## Architecture Principles

When contributing, respect these architectural boundaries:

### V3 Core (Frozen)
- `src/boardroom/governance.py` - Hard gates
- `src/boardroom/anchoring.py` - Hash chain
- `src/boardroom/roles.py` - Boardroom 13

Changes to V3 core require explicit governance approval.

### V4 Evolution Layer
- New automation handlers
- UI improvements
- Additional witness adapters
- Test coverage expansion

V4 changes must be **additive** and **non-breaking**.

## Testing Requirements

All PRs must:

1. Pass existing tests
2. Add tests for new functionality
3. Not reduce code coverage

Run tests locally:
```bash
cd sovereign-system
pytest tests/ -v
```

## Security

If you discover a security vulnerability, please see [SECURITY.md](SECURITY.md) for responsible disclosure guidelines.

## Questions?

Open a discussion issue or reach out to maintainers.

---

*"Evolution without erosion."*
