# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**Do not open a public issue.**

Report it privately through [GitHub security advisories](https://github.com/jaimefgdev/sounddiff/security/advisories/new) with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for a fix. Security patches are prioritized over all other work.

## Scope

sounddiff processes audio files from disk. Relevant security concerns include:

- Path traversal in file handling
- Denial of service via malformed audio files
- Dependency vulnerabilities
- Secret leakage in CI/CD

We run [gitleaks](https://github.com/gitleaks/gitleaks) in CI and as a pre-commit hook to prevent accidental secret commits.
