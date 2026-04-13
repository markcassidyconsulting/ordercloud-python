# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| Latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email **mark.cassidy@markcassidyconsulting.com** with:

- A description of the vulnerability
- Steps to reproduce or a proof of concept
- The potential impact

You will receive an acknowledgement within 48 hours and a detailed response within 5 business days, including next steps and any planned fixes.

If the vulnerability is confirmed, a fix will be developed and released as a patch version. A security advisory will be published via [GitHub Security Advisories](https://github.com/markcassidyconsulting/ordercloud-python/security/advisories) once a fix is available.

## Scope

This SDK is an HTTP client library. It does not run a server, store credentials persistently, or process untrusted input beyond what the OrderCloud API returns. Security concerns most likely relate to:

- Credential handling (OAuth tokens in memory)
- Dependency vulnerabilities (tracked via Dependabot and `dependency-review`)
- Injection via API response data (mitigated by Pydantic model validation)

## Security Measures

This project employs the following security practices:

- **Static analysis:** [CodeQL](https://github.com/markcassidyconsulting/ordercloud-python/actions/workflows/codeql.yml) runs on every push and weekly
- **Dependency scanning:** [Dependabot](https://github.com/markcassidyconsulting/ordercloud-python/security/dependabot) monitors for known vulnerabilities in dependencies
- **Dependency review:** Pull requests are checked for newly introduced vulnerable dependencies
- **Supply chain security:** All GitHub Actions are pinned to commit SHAs
- **Branch protection:** The `main` branch requires status checks to pass before merge
