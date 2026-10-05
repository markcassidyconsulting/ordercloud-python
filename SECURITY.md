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

## Logging

The SDK writes request log lines to the `ordercloud` logger (see [Structured Logging](README.md#structured-logging)). Path values that work as credentials, a password-reset `verificationCode` and an `invitationID`, appear in those lines as `***`. Every path-parameter name in the OrderCloud spec is classified as sensitive or not sensitive when the SDK is generated, and an unclassified name stops generation. Query parameters and request bodies are not written to these lines.

The SDK does not control what other code logs:

- **`httpx` logs the full URL.** For every request, `httpx` writes `HTTP Request: <METHOD> <URL> "<HTTP version> <status> <reason>"` at `INFO` on the `httpx` logger, with the full URL including the path and the query string (checked against the httpx 0.28.1 source). The line appears whenever that logger is enabled for `INFO`, for example after `logging.basicConfig(level=logging.INFO)` or `level=logging.DEBUG`. To keep it out of your logs:

  ```python
  import logging

  logging.getLogger("httpx").setLevel(logging.WARNING)
  ```

- **`httpx` exceptions carry the request.** Exceptions that `httpx` raises for transport failures (timeouts, connection errors) carry the request as their `request` attribute, and `exc.request.url` is the full URL.
- **Middleware hooks receive the concrete values.** `RequestContext.path`, `url` and `params` are the values sent to the API, and `headers` holds the `Authorization` bearer token. A hook that logs them must redact them itself.

## Security Measures

This project employs the following security practices:

- **Static analysis:** [CodeQL](https://github.com/markcassidyconsulting/ordercloud-python/actions/workflows/codeql.yml) runs on every push and weekly
- **Dependency scanning:** [Dependabot](https://github.com/markcassidyconsulting/ordercloud-python/security/dependabot) monitors for known vulnerabilities in dependencies
- **Dependency review:** Pull requests are checked for newly introduced vulnerable dependencies
- **Supply chain security:** All GitHub Actions are pinned to commit SHAs
- **Build provenance:** Every [GitHub release](https://github.com/markcassidyconsulting/ordercloud-python/releases) carries the build provenance attestation for its sdist and wheel as `ordercloud_python-<version>.intoto.jsonl`
- **Branch protection:** The `main` branch requires status checks to pass before merge

### Verifying a release

With the [GitHub CLI](https://cli.github.com/), download a release's files and check a distribution against its provenance file:

```bash
gh release download v<version> --repo markcassidyconsulting/ordercloud-python
gh attestation verify ordercloud_python-<version>-py3-none-any.whl --bundle ordercloud_python-<version>.intoto.jsonl --repo markcassidyconsulting/ordercloud-python
```

The provenance file covers both the wheel and the sdist (`ordercloud_python-<version>.tar.gz`), and the same command checks a wheel fetched from PyPI with `pip download ordercloud-python==<version> --no-deps`. Exit code 0 means the file matches build provenance signed by a GitHub Actions workflow in this repository; a modified file fails verification.
