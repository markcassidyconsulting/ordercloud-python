# Code Review — 13 April 2026

Comprehensive three-agent review of the entire codebase prior to initial PyPI release. Each agent reviewed a distinct area: hand-written infrastructure, generated code patterns, and tests/CI/codegen/config. All findings were triaged into fix, document, or dismiss.

**Methodology:** Three parallel review agents, each evaluating reuse, quality, efficiency, and security. 28 genuine findings identified. 12 fixed, 6 documented as known trade-offs, 10 dismissed with reasoning.

---

## Fixed

### Critical / High

**1. `HttpClient.delete()` had no query parameter support**
- The DELETE method signature was `async def delete(self, path: str)` with no way to pass query params. This made it structurally impossible for any generated DELETE method to send query parameters to the API.
- **Fix:** Added `**params` support to `delete()`, matching the existing `get()` pattern.

**2. ~25 `delete_assignment` methods silently discarded filter parameters**
- Methods like `products.delete_assignment(product_id, buyer_id, user_id=..., user_group_id=...)` accepted filter parameters in their signatures but never sent them to the API. The parameters were silently ignored.
- **Root cause:** The codegen resource template had no query parameter handling in the DELETE branch.
- **Fix:** Updated the resource template to build a `_params` dict from query parameters and pass them via `**_params` on DELETE calls. All 60 resource modules regenerated.

**3. Non-delete methods also silently discarded optional query parameters**
- Same pattern in other HTTP methods: `me.get_category(catalog_id=...)`, `categories.create(adjust_list_orders=...)`, `products.save_supplier(default_price_schedule_id=...)`, etc.
- **Root cause:** The template only handled query params for list methods. All other branches (GET, POST, PUT, PATCH) ignored them.
- **Fix:** Added query parameter collection and forwarding to all non-list branches in the resource template. Added `params` parameter to `post()`, `put()`, `patch()` in `HttpClient`.

### Medium

**4. `OrderCloudClient.create()` factory missing `max_retries` and `retry_backoff`**
- The convenience factory didn't expose retry configuration. The README's retry example (`OrderCloudClient.create(max_retries=3, retry_backoff=0.5)`) would raise `TypeError`.
- **Fix:** Added both parameters to the client template. `SyncOrderCloudClient.create()` already had them — now both factories are consistent.

**5. Stale bearer token on retries**
- The token was fetched once before the retry loop. After backoff delays (potentially several seconds), the same token was reused even if it had expired during the wait.
- **Fix:** Moved `get_token()` inside the retry loop so a fresh token is acquired on each attempt.

**6. Token refresh failure caused infinite retry loop**
- If `_refresh()` failed (expired refresh token, revoked grant), the old expired token remained cached. Subsequent `get_token()` calls would attempt refresh again, fail again, indefinitely.
- **Fix:** On `HTTPStatusError` during refresh, clear the cached token and fall back to full `client_credentials` authentication.

### Low

**7. No cap on `Retry-After` header value**
- A server sending `Retry-After: 999999` would block the client for ~11.5 days.
- **Fix:** Capped all retry delays (both `Retry-After` and exponential backoff) at 120 seconds.

**8. `scopes` list mutable despite `frozen=True` dataclass**
- `OrderCloudConfig` is a frozen dataclass, but `scopes: list[str]` allowed in-place mutation (`config.scopes.append(...)`) which violated the immutability contract.
- **Fix:** Changed type to `tuple[str, ...]` with a `__post_init__` that converts lists to tuples, so callers can pass either.

**9. SBOM workflow had overly broad `contents: write` permission**
- The job only uploads an artifact — no write access to repo contents is needed.
- **Fix:** Changed to `contents: read`.

**10. SECURITY.md version table said `0.1.x`**
- Stale from initial setup. Updated to `Latest` to avoid confusion with CalVer versioning.

**11. Mojibake in generated docstrings (Unicode apostrophes)**
- Smart quotes from the OpenAPI spec (`'` U+2019) were corrupted into multi-byte garble (`â€™`) in generated files.
- **Root cause:** `parser.py` opened the spec file with `open(spec_path)` — no explicit encoding. On Windows, this defaults to cp1252, which corrupts multi-byte UTF-8 characters.
- **Fix:** Changed to `open(spec_path, encoding="utf-8")`. Added `_clean_description()` as a safety net for specs that contain pre-existing mojibake.

**12. DELETE operations with return types generated no return statement**
- Two operations (`Orders.RemovePromotion` → `Order`, `OrderReturns.DeleteItem` → `OrderReturn`) declare a response body on DELETE but the template's DELETE branch unconditionally discarded the response.
- **Fix:** Split the template DELETE branch into `delete + return_type` (captures and returns response) and `delete + no return_type` (fire-and-forget).

**Additional fixes caught during validation:**
- Required query params (e.g. `UserOrderMoveOption` on `Users.Move`) were incorrectly defaulting to `None` in generated signatures. Fixed by conditionalising `= None` on `q.required` in the template.
- Client `create()` factories passed `list` to `scopes` where `tuple` was now expected. Fixed in both the template and `sync_client.py`.
- Middleware delegation methods (`add_before_request`, `add_after_response`) were missing from the client template. Added with proper imports.

---

## Known Trade-offs (not fixing)

**13. Retries on 500 for non-idempotent requests (POST/PUT/PATCH)**
- A 500 response doesn't guarantee the server didn't process the request. Retrying a POST could create duplicate resources.
- **Why not fixing:** Retries are disabled by default (`max_retries=0`). Users explicitly opt in. This is standard SDK behaviour — the official OrderCloud JS/C# SDKs don't restrict retry by HTTP method either. Documented in README.

**14. `exclude_none=True` prevents sending explicit null values**
- `model_dump(exclude_none=True)` strips all `None` values from request bodies. If a user sets a field to `None` to clear it server-side, the field is omitted instead of sent as `null`.
- **Why not fixing:** The alternative (`exclude_unset=True`) would require tracking which fields were explicitly set vs. defaulted, adding complexity to every model interaction. The current behavior produces clean request bodies for the overwhelming majority of use cases. Users needing explicit nulls can pass a raw dict instead of a model.

**15. `extra="allow"` round-trips unknown fields**
- The `OrderCloudModel` base class accepts unknown fields from API responses (forward-compatible with new API fields). When a model is serialised back to JSON for a PUT/PATCH, those unknown fields are included.
- **Why not fixing:** Forward compatibility is more important than preventing unknown field echo. The API will ignore fields it doesn't recognise. Breaking on new API fields would be worse.

**16. `authenticate_password()` not exposed on the public client API**
- The `TokenManager` has a password grant method, but neither `OrderCloudClient` nor `SyncOrderCloudClient` exposes it.
- **Why not fixing:** Password grant is a secondary authentication flow used for buyer-side impersonation. The v1 public API surface is intentionally minimal. Users needing password auth can construct a `TokenManager` directly or access `client._token_manager`.

**17. No URL path parameter encoding**
- Path segments are interpolated via f-strings without `urllib.parse.quote()`. An ID containing `/` or `?` could alter the request target.
- **Why not fixing:** OrderCloud IDs are API-controlled (assigned by the platform or validated on creation). They are alphanumeric strings, not user-supplied free text. The defence-in-depth concern is real but the risk is effectively zero for this API.

**18. Sensitive model fields (passwords, API keys) use plain `Optional[str]`**
- Fields like `User.Password`, `DeliveryConfig.ApiKey`, `KafkaConfig.SaslPassword` are plain strings. Pydantic's `repr()` and `model_dump()` will expose them.
- **Why not fixing:** Would require codegen enhancement to detect sensitive fields (via OpenAPI `format: password` or heuristic name matching) and emit `Field(repr=False)` or `SecretStr`. The OrderCloud spec doesn't consistently annotate these fields. Logged as a future codegen improvement.

---

## Dismissed (not issues)

**19. `asyncio.Lock()` created at `__init__` time may bind to wrong event loop**
- On Python 3.10+ (our minimum), `asyncio.Lock()` no longer binds to an event loop at construction. Non-issue.

**20. `_SyncProxy.__getattr__` creates a new wrapper closure on every access**
- HTTP I/O latency is 10-100ms per call. Closure allocation is ~100ns. Not a real bottleneck.

**21. `RequestContext` dict copies on every request**
- By design — middleware hooks receive mutable copies so they can modify headers/params without affecting subsequent retries. The copies are the feature.

**22. Event loop not set as running loop for the thread**
- `SyncOrderCloudClient` creates `asyncio.new_event_loop()` without `set_event_loop()`. This is intentional — setting it would be a thread-level side effect. No internal code calls `asyncio.get_event_loop()`.

**23. `mock_auth` fixture never activated as respx router**
- Test internals. The fixture exists for structural completeness but auth is bypassed by directly setting `_token`. Tests pass correctly. No user-facing impact.

**24. Unused `TOKEN_RESPONSE` constant in conftest**
- Dead test code. No functional impact.

**25. Redundant nested `respx.mock` context manager in one test**
- `test_hooks_via_client` had both a decorator and an inner context manager. Harmless — nested respx.mock is a no-op. No functional impact.

**26. `test_resource_coverage.py` duplicates config constants**
- Internal test organisation. The constants match conftest and would be caught by any drift that causes test failures.

**27. Per-test HttpClient construction in 632 parametrised tests**
- Each test case creates and tears down its own client. This is correct isolation. Total runtime is ~6 seconds for all 759 tests. Not a bottleneck.

**28. No negative tests for typed xp generics with invalid data**
- Testing Pydantic's own validation behaviour is out of scope. The SDK tests verify that the generic pattern works correctly for valid data. Pydantic's validation is tested by Pydantic.

---

## Upstream spec issues (cannot fix)

- **`categories.py` PATCH `adjustListOrders` description:** The OpenAPI spec contains `"Adjust list orders of the partial 1."` — garbled text from the upstream Sitecore spec. Not a codegen issue.

---

## Verification

After all fixes, full validation passed:
- **759 tests passing** (pytest, all Python versions)
- **Lint clean** (ruff check)
- **Format clean** (ruff format --check)
- **Type check clean** (mypy --strict)
- **97% coverage** maintained
