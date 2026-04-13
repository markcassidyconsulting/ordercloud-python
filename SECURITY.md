# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email **mark.cassidy@markcassidyconsulting.com** with:

- A description of the vulnerability
- Steps to reproduce or a proof of concept
- The potential impact

You will receive an acknowledgement within 48 hours and a detailed response within 5 business days, including next steps and any planned fixes.

## Scope

This SDK is an HTTP client library. It does not run a server, store credentials persistently, or process untrusted input beyond what the OrderCloud API returns. Security concerns most likely relate to:

- Credential handling (OAuth tokens in memory)
- Dependency vulnerabilities (tracked via Dependabot and `dependency-review`)
- Injection via API response data (mitigated by Pydantic model validation)
