# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| main    | ✅ Yes             |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities.
2. Instead, use [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) feature on this repository.
3. Provide a detailed description of the vulnerability, steps to reproduce, and potential impact.

We will acknowledge receipt within **48 hours** and aim to provide a fix or mitigation within **7 days** for critical issues.

## Security Best Practices

This project follows these security practices:

- Dependencies are audited in CI using `pip-audit`
- Code is linted with Ruff to catch common issues
- Type checking with mypy to reduce runtime errors
- All changes require CI to pass before merge
