# Security Policy

## Reporting Security Vulnerabilities

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**DO NOT** open a public issue for security vulnerabilities.

Instead:

1. Email security concerns to the repository maintainers
2. Include detailed information about the vulnerability
3. Provide steps to reproduce if possible
4. Allow time for assessment and remediation

### What to Include

- Description of the vulnerability
- Potential impact and severity
- Steps to reproduce
- Affected versions
- Suggested fixes (if any)

## Security Best Practices

When contributing to this project:

### Code Security

- Never commit secrets, API keys, or credentials
- Use environment variables for sensitive data
- Validate and sanitize all inputs
- Follow principle of least privilege

### Governance Security

- Keep threat models updated
- Document security assumptions
- Maintain audit trails in `evidence/`
- Follow phase gate reviews for security changes

### Dependencies

- Regularly update dependencies
- Review security advisories
- Use known secure versions
- Document dependency choices

## Security Monitoring

- All changes undergo security review
- Automated scanning in CI pipeline
- Regular security audits
- Threat model maintenance

## Incident Response

In case of a security incident:

1. Follow runbooks in `docs/templates/runbook_template.md`
2. Document evidence in `evidence/` directory
3. Update threat models with lessons learned
4. Communicate with stakeholders

## Supported Versions

This is a scaffold repository. Security support applies to the latest main branch.

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report vulnerabilities.
