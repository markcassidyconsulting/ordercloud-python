"""Tests for the middleware context types."""

from __future__ import annotations

import dataclasses

import httpx
import pytest

from ordercloud.middleware import RequestContext, ResponseContext

TOKEN = "secret-token"
URL = "https://api.ordercloud.io/v1/me"


def _context(headers: dict[str, str] | None = None) -> RequestContext:
    if headers is None:
        headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    return RequestContext(method="GET", path="/me", url=URL, headers=headers)


def _renderings(obj: object) -> tuple[str, ...]:
    return (repr(obj), str(obj), f"{obj}", "%r" % (obj,), "%s" % (obj,))


class _UnreadableHeaders(dict):
    """A headers mapping whose items cannot be read."""

    def items(self):  # type: ignore[override]
        raise RuntimeError("unreadable")


# ---------------------------------------------------------------------------
# RequestContext repr
# ---------------------------------------------------------------------------


class TestRequestContextRepr:
    def test_repr_and_str_redact_authorization(self):
        for rendered in _renderings(_context()):
            assert TOKEN not in rendered
            assert "'Authorization': '***'" in rendered
            assert "'Accept': 'application/json'" in rendered

    def test_repr_keeps_dataclass_format(self):
        ctx = RequestContext(
            method="POST",
            path="/products",
            url="https://api.ordercloud.io/v1/products",
            headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"},
            params={"pageSize": 100},
            json={"ID": "p1"},
        )
        assert repr(ctx) == (
            "RequestContext(method='POST', path='/products', "
            "url='https://api.ordercloud.io/v1/products', "
            "headers={'Authorization': '***', 'Accept': 'application/json'}, "
            "params={'pageSize': 100}, json={'ID': 'p1'})"
        )

    @pytest.mark.parametrize("key", ["authorization", "AUTHORIZATION", "aUtHoRiZaTiOn"])
    def test_authorization_key_matched_case_insensitively(self, key: str):
        rendered = repr(_context({key: f"Bearer {TOKEN}"}))
        assert TOKEN not in rendered
        assert f"{key!r}: '***'" in rendered

    def test_bytes_authorization_key_redacted(self):
        headers = {b"Authorization": f"Bearer {TOKEN}".encode()}
        rendered = repr(_context(headers))  # type: ignore[arg-type]
        assert TOKEN not in rendered
        assert "b'Authorization': '***'" in rendered

    def test_header_added_after_construction_is_redacted(self):
        ctx = _context({"Accept": "application/json"})
        assert "***" not in repr(ctx)
        ctx.headers["Authorization"] = f"Bearer {TOKEN}"
        assert TOKEN not in repr(ctx)
        assert "'Authorization': '***'" in repr(ctx)

    def test_replaced_headers_dict_is_redacted(self):
        ctx = _context({"Accept": "application/json"})
        ctx.headers = {"Authorization": f"Bearer {TOKEN}"}
        assert TOKEN not in repr(ctx)

    def test_repr_does_not_mutate_headers(self):
        headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
        ctx = _context(headers)
        repr(ctx)
        str(ctx)
        assert ctx.headers is headers
        assert ctx.headers == {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

    def test_headers_without_authorization_render_unredacted(self):
        ctx = _context({"Accept": "application/json", "X-Correlation-ID": "abc-123"})
        rendered = repr(ctx)
        assert "headers={'Accept': 'application/json', 'X-Correlation-ID': 'abc-123'}" in rendered
        assert "***" not in rendered

    def test_empty_headers_render_as_empty_dict(self):
        ctx = RequestContext(method="GET", path="/me", url=URL)
        assert "headers={}" in repr(ctx)

    @pytest.mark.parametrize(
        "headers",
        [f"Bearer {TOKEN}", [("Authorization", f"Bearer {TOKEN}")], None],
        ids=["str", "list-of-pairs", "none"],
    )
    def test_non_mapping_headers_render_as_redacted(self, headers: object):
        ctx = _context()
        ctx.headers = headers  # type: ignore[assignment]
        for rendered in _renderings(ctx):
            assert TOKEN not in rendered
            assert "headers='***'" in rendered

    def test_unreadable_headers_render_as_redacted(self):
        ctx = _context(_UnreadableHeaders({"Authorization": f"Bearer {TOKEN}"}))
        rendered = repr(ctx)
        assert TOKEN not in rendered
        assert "headers='***'" in rendered

    def test_self_referencing_headers_do_not_recurse(self):
        ctx = _context()
        ctx.headers["X-Context"] = ctx  # type: ignore[assignment]
        rendered = repr(ctx)
        assert TOKEN not in rendered
        assert "'X-Context': ..." in rendered

    def test_equality_replace_and_fields_unchanged(self):
        ctx = _context()
        assert dataclasses.replace(ctx) == ctx
        assert ctx == _context()
        assert ctx.headers["Authorization"] == f"Bearer {TOKEN}"
        assert dataclasses.asdict(ctx)["headers"]["Authorization"] == f"Bearer {TOKEN}"


# ---------------------------------------------------------------------------
# ResponseContext repr
# ---------------------------------------------------------------------------


class TestResponseContextRepr:
    def test_repr_delegates_to_redacted_request(self):
        resp_ctx = ResponseContext(request=_context(), response=httpx.Response(200), attempt=0)
        for rendered in _renderings(resp_ctx):
            assert TOKEN not in rendered
            assert rendered.startswith("ResponseContext(request=RequestContext(")
            assert "'Authorization': '***'" in rendered
