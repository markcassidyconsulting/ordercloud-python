# Security Audit — 13 April 2026

## Audit Prompt

The following prompt was used verbatim to task a Claude Opus agent with a comprehensive security audit of this codebase:

> You are a senior application security engineer conducting a comprehensive security audit. Analyze the provided application code against the following standards and frameworks:
>
> **OWASP Top 10 (2021)**
> Check for: Broken Access Control, Cryptographic Failures, Injection, Insecure Design, Security Misconfiguration, Vulnerable/Outdated Components, Identification & Authentication Failures, Software & Data Integrity Failures, Security Logging & Monitoring Failures, Server-Side Request Forgery.
>
> **CWE/SANS Top 25 Most Dangerous Software Weaknesses**
> Check for: Out-of-bounds Write, XSS, SQL Injection, Use After Free, OS Command Injection, Improper Input Validation, Out-of-bounds Read, Path Traversal, CSRF, Unrestricted File Upload, Missing Authorization, NULL Pointer Dereference, Improper Authentication, Integer Overflow, Deserialization of Untrusted Data, Command Injection, Improper Restriction of Operations within Memory Buffer, Missing Authentication for Critical Function, Incorrect Default Permissions, Improper Limitation of Pathname, Incorrect Calculation of Buffer Size, Exposure of Sensitive Information, Heap-based Buffer Overflow, Use of Hard-coded Credentials, Uncontrolled Resource Consumption.
>
> **Additional checks:**
> - NIST SP 800-53 relevant controls (AC, AU, IA, SC, SI families)
> - Secrets management (hardcoded keys, tokens, passwords, API keys)
> - Dependency vulnerabilities (known CVEs in imported packages)
> - Data exposure (PII leaks, verbose errors, debug endpoints)
> - Authentication & session management flaws
> - Rate limiting and DoS resilience
> - TLS/encryption implementation correctness
> - Privilege escalation vectors
> - Supply chain attack surface
>
> **For each finding, report:**
> 1. Severity: Critical / High / Medium / Low / Informational
> 2. CWE ID (where applicable)
> 3. Affected file(s) and line(s)
> 4. Description of the vulnerability
> 5. Proof of concept or attack scenario
> 6. Recommended fix with code example
> 7. Applicable standard reference (OWASP/CWE/NIST)
>
> **Output format:** Start with an executive summary and risk score (0-10). Then list findings grouped by severity. End with a prioritized remediation roadmap.

---

## Executive Summary

**Overall Risk Score: 2.5 / 10 (Low)**

This is a well-constructed, security-conscious client-side SDK for the Sitecore OrderCloud API. The codebase follows modern Python best practices: frozen dataclasses for configuration, Pydantic v2 for data validation, pinned dependencies with SHA-based GitHub Actions, and comprehensive CI/CD security tooling (CodeQL, Scorecard, Dependabot, SBOM, dependency review).

The SDK is a *client library*, not a server application. It does not accept external input from untrusted sources, does not serve HTTP endpoints, does not interact with filesystems, and does not execute user-supplied code. This fundamentally limits the attack surface. Most OWASP Top 10 and CWE/SANS Top 25 categories (XSS, SQL injection, CSRF, file upload, buffer overflows, etc.) are structurally inapplicable.

**Zero Critical or High findings.**

---

## Findings

### MEDIUM

#### M1: Credential Exposure in `.env` File (Local Development Risk)

- **Severity:** Medium
- **CWE:** CWE-798 (Use of Hard-coded Credentials) / CWE-522 (Insufficiently Protected Credentials)
- **Affected file:** `.env` (lines 1-4)
- **OWASP:** A07:2021 Identification and Authentication Failures
- **NIST:** IA-5 (Authenticator Management)

**Description:** The `.env` file contains OrderCloud sandbox credentials. The file is listed in `.gitignore` and is confirmed not tracked by git. However, it exists on disk in the project root alongside tracked files.

**Attack scenario:** If the `.gitignore` entry were accidentally removed, or if the repository were copied/archived without respecting gitignore, these credentials would be exposed.

**Recommended fix:** Consider rotating the sandbox credentials. For defense in depth, add `.env` to a `.gitignore` comment explaining it must never be committed.

**Disposition:** Not actioned. The `.env` file has never been committed to version control and has never existed outside the developer's local machine. There is no exposure event that would warrant credential rotation. The gitignore entry provides adequate protection for a local sandbox credential. Rotating credentials that were never exposed is security theater.

---

#### M2: `OrderCloudConfig` Lacks `__repr__` Redaction — Credentials Visible in Logs/Tracebacks

- **Severity:** Medium
- **CWE:** CWE-532 (Insertion of Sensitive Information into Log File)
- **Affected file:** `src/ordercloud/config.py` (lines 8-34), `src/ordercloud/auth.py`
- **OWASP:** A09:2021 Security Logging and Monitoring Failures
- **NIST:** AU-3 (Content of Audit Records), SI-11 (Error Handling)

**Description:** `OrderCloudConfig` is a `@dataclass(frozen=True)` which auto-generates `__repr__` that includes all fields, including `client_secret`. If an `OrderCloudConfig` instance appears in a traceback, log message, or debugging output, the `client_secret` will be printed in cleartext. Similarly, `AccessToken` in `auth.py` stores `access_token` and `refresh_token` as plain attributes with no `__repr__` override.

**Attack scenario:** An unhandled exception during initialization or debugging could print `OrderCloudConfig(client_id='...', client_secret='realSecret123', ...)` to stderr, a log aggregator, or an error monitoring service.

**Disposition:** Fixed. Added `__repr__` overrides that mask `client_secret` on `OrderCloudConfig` and `access_token`/`refresh_token` on `AccessToken`.

---

#### M3: No URL Validation on `base_url` / `auth_url` — SSRF via Configuration

- **Severity:** Medium
- **CWE:** CWE-918 (Server-Side Request Forgery)
- **Affected files:** `src/ordercloud/config.py` (lines 25-26), `src/ordercloud/http.py`, `src/ordercloud/auth.py`
- **OWASP:** A10:2021 Server-Side Request Forgery
- **NIST:** SC-7 (Boundary Protection)

**Description:** The `base_url` and `auth_url` config parameters accept arbitrary strings with no validation. If set to an attacker-controlled URL (e.g. via environment variable injection), the SDK would send authenticated requests including bearer tokens to that endpoint.

**Attack scenario:** In a deployment where `base_url` is read from an environment variable, an attacker who can modify that variable (container escape, CI injection, etc.) could redirect all API calls and the OAuth2 token to a malicious server.

**Disposition:** Not actioned. This is by design. OrderCloud supports multiple regional endpoints (US, Europe West, Australia East, Japan East, plus sandbox variants). Users must be able to point the SDK at any of these. Adding domain allowlists would break legitimate deployments and impose maintenance burden as Sitecore adds new regions. If an attacker has the ability to modify environment variables in your runtime, URL validation is not your most pressing problem.

---

### LOW

#### L1: `python-dotenv` as Runtime Dependency — Unnecessary Attack Surface

- **Severity:** Low
- **CWE:** CWE-1104 (Use of Unmaintained Third-Party Components) — tangential
- **Affected file:** `pyproject.toml` (line 42)
- **OWASP:** A06:2021 Vulnerable and Outdated Components
- **NIST:** SA-11 (Developer Security and Privacy Architecture)

**Description:** `python-dotenv` is declared as a runtime dependency but is only used in `examples/basic_workflow.py`. The core SDK never imports it. Every user who installs the SDK also installs `python-dotenv` even though it is not needed for SDK operation.

**Disposition:** Fixed. Moved to optional `examples` dependency group.

---

#### L2: `Retry-After` Header Parsing Accepts Large Values (Capped at 120s)

- **Severity:** Low
- **CWE:** CWE-400 (Uncontrolled Resource Consumption)
- **Affected file:** `src/ordercloud/http.py` (lines 150-158)
- **NIST:** SC-5 (Denial of Service Protection)

**Description:** A malicious server could set `Retry-After: 120` on every response, causing the client to sleep up to `120 * max_retries` seconds. With `max_retries=3`, that's 6 minutes of blocking.

**Disposition:** Already mitigated. The 120-second cap was added during the code review phase. The user configures `max_retries` themselves (default 0 = disabled). Acceptable residual risk.

---

#### L3: `OrderCloudError.raw` Exposes Full API Error Response Body

- **Severity:** Low
- **CWE:** CWE-209 (Generation of Error Message Containing Sensitive Information)
- **Affected file:** `src/ordercloud/errors.py` (lines 38-43)
- **OWASP:** A04:2021 Insecure Design
- **NIST:** SI-11 (Error Handling)

**Description:** `OrderCloudError` stores the complete raw JSON response body. If the API returns sensitive data in error responses, this propagates through exception handling and could be logged.

**Disposition:** Not actioned. This is standard SDK behaviour. The SDK's job is to faithfully convey API responses, including errors. Redacting error bodies would impair debugging and violate the principle of least surprise. Consumer applications are responsible for their own logging policies.

---

### INFORMATIONAL (Positive Findings)

**I1: CI workflow actions correctly pinned by SHA.** All GitHub Actions use full commit SHAs, not mutable tags. Dependabot manages SHA updates. Best practice for supply chain security.

**I2: Release pipeline uses OIDC trusted publishing.** No stored PyPI API token — eliminates credential theft risk from the release pipeline. Build provenance attestation included via Sigstore.

**I3: Minimal per-job permissions in all workflows.** All workflows declare explicit `permissions:` blocks. The release workflow starts with `permissions: {}` and grants specific permissions per job. Principle of least privilege.

**I4: Codegen subprocess call is safe.** `subprocess.run(["ruff", "format", *paths], ...)` uses list-form arguments (no `shell=True`). Paths are derived from internal deterministic grouping, not external input.

**I5: Codegen template injection not applicable.** Data flows from a trusted JSON file through parser to Jinja2 templates. Templates do not use `| safe` on external data. The OpenAPI spec is a trusted, version-controlled input.

**I6: `extra="allow"` on Pydantic models is intentional and safe.** Forward-compatible with API additions. Does not create a security vulnerability in a client library context.

---

## Non-Applicable Categories

| Category | Reason |
|----------|--------|
| A03 Injection (SQL, OS Command, XSS) | SDK does not interact with databases, OS commands, or render HTML |
| A08 Software & Data Integrity (Deserialization) | Uses Pydantic `model_validate`, not `pickle`/`marshal`/`yaml.load` |
| CWE-22 Path Traversal | SDK does not interact with filesystems |
| CWE-434 Unrestricted File Upload | No file upload functionality |
| CWE-352 CSRF | Client library, not a server |
| CWE-190 Integer Overflow | Python handles arbitrary-precision integers |
| CWE-787/125 Buffer Overflow | Python is a memory-safe language |

---

## Verification

All fixes validated: 759 tests passing, lint clean, format clean, mypy strict clean, 97% coverage maintained.
