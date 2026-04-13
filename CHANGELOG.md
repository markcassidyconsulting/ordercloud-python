# Changelog

All notable changes to this project will be documented in this file.

This project uses [Calendar Versioning](https://calver.org/) — `YYYY.MM.N` where `N` is the release number within that month.

## 2026.4.1 — 2026-04-13

Initial release. Full SDK for the Sitecore OrderCloud API, generated from the OpenAPI v3 spec (version 1.0.445).

### Features

- **Full API coverage** — 632 operations across 60 resources, generated from the official OpenAPI spec
- **Async and sync clients** — `OrderCloudClient` (async, default) and `SyncOrderCloudClient` with identical API shapes
- **Pydantic v2 typed models** — 167 models and 17 enums with full type annotations
- **Typed extended properties (xp)** — `Product[MyXp]` pattern for type-safe custom fields, backward compatible with untyped `dict[str, Any]`
- **Auto-pagination** — `paginate()` and `paginate_sync()` async/sync generators for any list method
- **Retry with exponential backoff** — configurable `max_retries` and `retry_backoff`; retries 429/5xx, respects `Retry-After` headers
- **Structured logging** — `logging.getLogger("ordercloud")` with DEBUG request/response and WARNING retry logging
- **Middleware hooks** — `add_before_request()` / `add_after_response()` for request/response interception
- **OAuth2 client credentials** — automatic token acquisition, caching, and refresh
- **PEP 561 typed** — `py.typed` marker for downstream type checking

### Code Generation

Three-stage pipeline in `tools/codegen/`: OpenAPI JSON -> parser -> IR dataclasses -> transformer -> Jinja2 templates -> Python source -> ruff format. 10 source files, 5 templates. Generates 100 files (37 model modules, 60 resource modules, 2 init barrels, 1 client).

### Quality

- 759 unit tests, 97% overall coverage (100% on all hand-written infrastructure and all 37 model modules)
- CI: lint, format, type check (mypy strict), test matrix (Python 3.10-3.13), coverage upload
- CodeQL security scanning, OpenSSF Scorecard, SBOM generation, dependency review
- Dependabot for pip and GitHub Actions version management
- Branch protection with required status checks
