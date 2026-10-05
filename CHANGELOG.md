# Changelog

All notable changes to this project will be documented in this file.

This project uses [Calendar Versioning](https://calver.org/) — `YYYY.MM.N` where `N` is the release number within that month.

## 2026.10.1 — 2026-10-05

Regenerated from the OrderCloud OpenAPI v3 spec, **version 1.0.454 → 1.0.470**. This release contains **one breaking change** — `ApiClient.client_secret` is removed — which the CalVer version number does not signal. Coverage is unchanged: **639 operations** across 60 resources, with 173 models and 17 enums.

### Breaking

- **`ApiClient.client_secret` (`ClientSecret`) removed**, following its removal from the `ApiClient` schema in the spec. `ApiClient` keeps the models' `extra="allow"` configuration, so code that still uses the field now behaves as follows:
  - Reading `.client_secret` on an `ApiClient` that was not given one raises `AttributeError` (it previously returned `None`).
  - mypy reports any `.client_secret` access as an `attr-defined` error.
  - A `ClientSecret` value in an API response is no longer available as `.client_secret`; it is kept as an undeclared extra under its API name, in `model_extra["ClientSecret"]`.
  - `ApiClient(ClientSecret="...")` is accepted, and the value is still sent to the API under the key `ClientSecret`.
  - `ApiClient(client_secret="...")` is accepted, but the value is now sent to the API under the snake_case key `client_secret` instead of `ClientSecret`.
  - Request bodies passed as plain dicts are sent unchanged.

  The five API-client secret operations (`ApiClients.ListSecrets` / `CreateSecret` / `GetSecret` / `PatchSecret` / `DeleteSecret`) and the `ApiClientSecret` / `ApiClientSecretCreateResponse` models are unchanged in this release.

### Added

- **`Discount.priority`** (`Priority`, integer). The spec describes it as: "Controls precedence when multiple discounts apply to the same user and product. Lower number = higher precedence (1 beats 2). Null is applied last."
- **`OrderEditAfterSubmit`** added to the `ApiRole` enum. Role lists that contain it (for example `SecurityProfile.roles` or `ApiClient.maximum_granted_roles`) now validate; on 2026.6.1 they raise a pydantic `ValidationError`.

### Spec changes with no SDK code change

- The `x-lifecycle: Beta` marker is removed from the Discounts tag and its nine operations. The code generator does not read this marker.
- `GET /discounts` now lists `Priority` and `!Priority` as `sortBy` values. `Discounts.list` takes `sort_by` as a plain string and passes it through unvalidated, so no SDK change was needed.
- `OrderEditAfterSubmit` is also added to the spec's OAuth2 scopes. The SDK's `scopes` setting takes plain strings.

### Release artefacts

- GitHub releases now also attach the build provenance attestation for the sdist and wheel, as `ordercloud_python-<version>.intoto.jsonl`, alongside the distributions themselves.

### Changed

- Bumped package version to `2026.10.1` (CalVer).

## 2026.6.1 — 2026-06-14

Regenerated from the OrderCloud OpenAPI v3 spec, **version 1.0.445 → 1.0.454**. All changes are additive — no breaking changes to existing models or operations. Coverage now spans **639 operations** (was 632) across the same 60 resources, with **173 models** and 17 enums.

### Added

- **Generated promotion codes** — `Promotions.ListCodes` (`GET /promotions/{promotionID}/codes`), the `PromotionCode` model, and `GeneratedCodeCount` / `GeneratedCodeLength` / `GeneratedCodePrefix` fields on the `Promotion` model family (`Promotion`, `OrderPromotion`, `AddedPromo`, `RemovedPromo`, `EligiblePromotion`).
- **Repeat order** — `Orders.Repeat` (`POST /orders/{direction}/{orderID}/repeat`) with the `OrderRepeatResponse` and `UnavailableLineItem` models.
- **Catalog entity sync** — five `EntitySyncs` catalog operations (get / save / patch / delete on `/integrations/entitysync/catalogs`, plus `/catalogs/sync`) and the `SyncCatalog` model.
- **New models** — `BuyerDiscount` (on `BuyerPriceSchedule`) and `ApiError` (the typed error returned within `UnavailableLineItem`).
- **New fields / values** — `Percent` on `DiscountedPrices`; `BulkReader` added to the `ApiRole` enum.

### Changed

- Bumped package version to `2026.6.1` (CalVer).

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
