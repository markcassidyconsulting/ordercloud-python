"""Tests for the HTTP client, error handling, retry logic, logging, and middleware."""

from __future__ import annotations

import logging

import pytest
import respx
from httpx import Response

from ordercloud.errors import AuthenticationError, OrderCloudError
from ordercloud.http import HttpClient
from ordercloud.middleware import RequestContext, ResponseContext

from .conftest import TEST_BASE_URL


# ---------------------------------------------------------------------------
# Request building
# ---------------------------------------------------------------------------


class TestRequestBuilding:
    @respx.mock
    async def test_get_sends_bearer_token(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))
        await http_client.get("/products")
        assert route.calls[0].request.headers["authorization"] == "Bearer mock-token-12345"

    @respx.mock
    async def test_get_builds_correct_url(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products/my-id").mock(
            return_value=Response(200, json={})
        )
        await http_client.get("/products/my-id")
        assert route.called

    @respx.mock
    async def test_get_passes_query_params(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))
        await http_client.get("/products", search="widget", page=1, pageSize=20)
        url = route.calls[0].request.url
        assert "search=widget" in str(url)
        assert "page=1" in str(url)
        assert "pageSize=20" in str(url)

    @respx.mock
    async def test_get_strips_none_params(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))
        await http_client.get("/products", search="widget", sortBy=None)
        url = str(route.calls[0].request.url)
        assert "search=widget" in url
        assert "sortBy" not in url

    @respx.mock
    async def test_post_sends_json_body(self, http_client: HttpClient):
        route = respx.post(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(201, json={"ID": "new"})
        )
        await http_client.post("/products", json={"Name": "Widget", "Active": True})
        body = route.calls[0].request.content.decode()
        assert '"Name"' in body
        assert '"Active"' in body

    @respx.mock
    async def test_put_sends_json_body(self, http_client: HttpClient):
        route = respx.put(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1"})
        )
        await http_client.put("/products/p1", json={"Name": "Updated"})
        assert route.called

    @respx.mock
    async def test_patch_sends_json_body(self, http_client: HttpClient):
        route = respx.patch(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1"})
        )
        await http_client.patch("/products/p1", json={"Name": "Patched"})
        assert route.called

    @respx.mock
    async def test_delete_sends_no_body(self, http_client: HttpClient):
        route = respx.delete(f"{TEST_BASE_URL}/products/p1").mock(return_value=Response(204))
        await http_client.delete("/products/p1")
        assert route.called


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    @respx.mock
    async def test_401_raises_authentication_error(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                401,
                json={"Errors": [{"ErrorCode": "Auth.Unauthorized", "Message": "Invalid token"}]},
            )
        )
        with pytest.raises(AuthenticationError) as exc_info:
            await http_client.get("/products")
        assert exc_info.value.status_code == 401
        assert exc_info.value.errors[0].error_code == "Auth.Unauthorized"

    @respx.mock
    async def test_403_raises_authentication_error(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                403,
                json={"Errors": [{"ErrorCode": "Auth.Forbidden", "Message": "Insufficient roles"}]},
            )
        )
        with pytest.raises(AuthenticationError) as exc_info:
            await http_client.get("/products")
        assert exc_info.value.status_code == 403

    @respx.mock
    async def test_404_raises_ordercloud_error(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products/nope").mock(
            return_value=Response(
                404,
                json={"Errors": [{"ErrorCode": "NotFound", "Message": "Product not found"}]},
            )
        )
        with pytest.raises(OrderCloudError) as exc_info:
            await http_client.get("/products/nope")
        assert exc_info.value.status_code == 404
        assert not isinstance(exc_info.value, AuthenticationError)

    @respx.mock
    async def test_400_raises_with_multiple_errors(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                400,
                json={
                    "Errors": [
                        {"ErrorCode": "Validation.Required", "Message": "Name is required"},
                        {"ErrorCode": "Validation.Invalid", "Message": "ID too long"},
                    ]
                },
            )
        )
        with pytest.raises(OrderCloudError) as exc_info:
            await http_client.post("/products", json={})
        assert len(exc_info.value.errors) == 2
        assert exc_info.value.errors[0].error_code == "Validation.Required"
        assert exc_info.value.errors[1].error_code == "Validation.Invalid"

    @respx.mock
    async def test_409_conflict(self, http_client: HttpClient):
        respx.put(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(
                409,
                json={"Errors": [{"ErrorCode": "Conflict", "Message": "Already exists"}]},
            )
        )
        with pytest.raises(OrderCloudError) as exc_info:
            await http_client.put("/products/p1", json={})
        assert exc_info.value.status_code == 409

    @respx.mock
    async def test_500_raises_ordercloud_error(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(500, text="Internal Server Error")
        )
        with pytest.raises(OrderCloudError) as exc_info:
            await http_client.get("/products")
        assert exc_info.value.status_code == 500
        # Non-JSON body should still produce an error.
        assert exc_info.value.errors[0].error_code == "Unknown"

    @respx.mock
    async def test_error_preserves_raw_body(self, http_client: HttpClient):
        raw = {"Errors": [{"ErrorCode": "Test", "Message": "test error", "Data": {"extra": 1}}]}
        respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(400, json=raw))
        with pytest.raises(OrderCloudError) as exc_info:
            await http_client.get("/products")
        assert exc_info.value.raw == raw
        assert exc_info.value.errors[0].data == {"extra": 1}

    @respx.mock
    async def test_error_message_formatting(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                404,
                json={"Errors": [{"ErrorCode": "NotFound", "Message": "Not found"}]},
            )
        )
        with pytest.raises(OrderCloudError, match="OrderCloud 404: Not found"):
            await http_client.get("/products")


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------


class TestRetryLogic:
    @respx.mock
    async def test_retries_on_500(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(500, text="Internal Server Error"),
                Response(200, json={"Items": []}),
            ]
        )
        resp = await retry_http_client.get("/products")
        assert resp.status_code == 200
        assert route.call_count == 2

    @respx.mock
    async def test_retries_on_429(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(429, text="Rate limited"),
                Response(200, json={}),
            ]
        )
        resp = await retry_http_client.get("/products")
        assert resp.status_code == 200
        assert route.call_count == 2

    @respx.mock
    async def test_retries_on_502(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(502, text="Bad Gateway"),
                Response(200, json={}),
            ]
        )
        resp = await retry_http_client.get("/products")
        assert resp.status_code == 200
        assert route.call_count == 2

    @respx.mock
    async def test_retries_on_503(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(503, text="Service Unavailable"),
                Response(200, json={}),
            ]
        )
        resp = await retry_http_client.get("/products")
        assert resp.status_code == 200
        assert route.call_count == 2

    @respx.mock
    async def test_retries_on_504(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(504, text="Gateway Timeout"),
                Response(200, json={}),
            ]
        )
        resp = await retry_http_client.get("/products")
        assert resp.status_code == 200
        assert route.call_count == 2

    @respx.mock
    async def test_no_retry_on_400(self, retry_http_client: HttpClient):
        route = respx.post(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                400,
                json={"Errors": [{"ErrorCode": "Validation", "Message": "Bad request"}]},
            )
        )
        with pytest.raises(OrderCloudError) as exc_info:
            await retry_http_client.post("/products", json={})
        assert exc_info.value.status_code == 400
        assert route.call_count == 1

    @respx.mock
    async def test_no_retry_on_401(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                401,
                json={"Errors": [{"ErrorCode": "Auth", "Message": "Unauthorized"}]},
            )
        )
        with pytest.raises(AuthenticationError):
            await retry_http_client.get("/products")
        assert route.call_count == 1

    @respx.mock
    async def test_no_retry_on_404(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products/nope").mock(
            return_value=Response(
                404,
                json={"Errors": [{"ErrorCode": "NotFound", "Message": "Not found"}]},
            )
        )
        with pytest.raises(OrderCloudError):
            await retry_http_client.get("/products/nope")
        assert route.call_count == 1

    @respx.mock
    async def test_raises_after_max_retries_exhausted(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(500, text="Internal Server Error"),
        )
        with pytest.raises(OrderCloudError) as exc_info:
            await retry_http_client.get("/products")
        assert exc_info.value.status_code == 500
        # 1 initial + 3 retries = 4 total attempts
        assert route.call_count == 4

    @respx.mock
    async def test_retry_succeeds_on_last_attempt(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(500, text="fail"),
                Response(503, text="fail"),
                Response(502, text="fail"),
                Response(200, json={"ok": True}),
            ]
        )
        resp = await retry_http_client.get("/products")
        assert resp.status_code == 200
        assert route.call_count == 4

    @respx.mock
    async def test_no_retry_when_disabled(self, http_client: HttpClient):
        """Default config has max_retries=0, so no retries."""
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(500, text="fail"),
        )
        with pytest.raises(OrderCloudError):
            await http_client.get("/products")
        assert route.call_count == 1

    @respx.mock
    async def test_respects_retry_after_header(self, retry_http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(429, text="Rate limited", headers={"Retry-After": "0"}),
                Response(200, json={}),
            ]
        )
        resp = await retry_http_client.get("/products")
        assert resp.status_code == 200
        assert route.call_count == 2


# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------


class TestLogging:
    @respx.mock
    async def test_logs_request_and_response(
        self, http_client: HttpClient, caplog: pytest.LogCaptureFixture
    ):
        respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))
        with caplog.at_level(logging.DEBUG, logger="ordercloud"):
            await http_client.get("/products")
        messages = [r.message for r in caplog.records]
        assert any("Request: GET /products" in m for m in messages)
        assert any("Response: GET /products 200" in m for m in messages)

    @respx.mock
    async def test_logs_retry_warning(
        self, retry_http_client: HttpClient, caplog: pytest.LogCaptureFixture
    ):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(503, text="down"),
                Response(200, json={}),
            ]
        )
        with caplog.at_level(logging.WARNING, logger="ordercloud"):
            await retry_http_client.get("/products")
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "Retry 1/3" in warnings[0].message
        assert "503" in warnings[0].message


# ---------------------------------------------------------------------------
# Middleware hooks
# ---------------------------------------------------------------------------


class TestMiddleware:
    @respx.mock
    async def test_before_request_adds_header(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))

        async def add_correlation_id(ctx: RequestContext) -> None:
            ctx.headers["X-Correlation-ID"] = "test-123"

        http_client.add_before_request(add_correlation_id)
        await http_client.get("/products")
        assert route.calls[0].request.headers["x-correlation-id"] == "test-123"

    @respx.mock
    async def test_before_request_modifies_params(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))

        async def force_page_size(ctx: RequestContext) -> None:
            if ctx.params is None:
                ctx.params = {}
            ctx.params["pageSize"] = 100

        http_client.add_before_request(force_page_size)
        await http_client.get("/products", search="test")
        url = str(route.calls[0].request.url)
        assert "pageSize=100" in url

    @respx.mock
    async def test_after_response_receives_context(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))

        captured: list[ResponseContext] = []

        async def capture(ctx: ResponseContext) -> None:
            captured.append(ctx)

        http_client.add_after_response(capture)
        await http_client.get("/products")

        assert len(captured) == 1
        assert captured[0].request.method == "GET"
        assert captured[0].request.path == "/products"
        assert captured[0].response.status_code == 200
        assert captured[0].attempt == 0

    @respx.mock
    async def test_after_response_called_on_each_retry(self, retry_http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(500, text="fail"),
                Response(200, json={}),
            ]
        )

        attempts: list[int] = []

        async def track_attempts(ctx: ResponseContext) -> None:
            attempts.append(ctx.attempt)

        retry_http_client.add_after_response(track_attempts)
        await retry_http_client.get("/products")

        assert attempts == [0, 1]

    @respx.mock
    async def test_multiple_hooks_run_in_order(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))

        order: list[str] = []

        async def hook_a(ctx: RequestContext) -> None:
            order.append("a")

        async def hook_b(ctx: RequestContext) -> None:
            order.append("b")

        http_client.add_before_request(hook_a)
        http_client.add_before_request(hook_b)
        await http_client.get("/products")

        assert order == ["a", "b"]

    @respx.mock
    async def test_hooks_via_client(self, config):
        """Verify hooks can be registered through OrderCloudClient."""
        from ordercloud import OrderCloudClient
        from ordercloud.auth import AccessToken

        client = OrderCloudClient(config)
        client._token_manager._token = AccessToken("mock-token-12345", expires_in=600)

        captured: list[ResponseContext] = []

        async def capture(ctx: ResponseContext) -> None:
            captured.append(ctx)

        client.add_after_response(capture)

        respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))

        async with respx.mock:
            await client._http.get("/products")

        assert len(captured) == 1
        await client.close()

    @respx.mock
    async def test_hooks_via_client_before_request(self, config):
        """Verify before-request hooks registered through OrderCloudClient."""
        from ordercloud import OrderCloudClient
        from ordercloud.auth import AccessToken

        client = OrderCloudClient(config)
        client._token_manager._token = AccessToken("mock-token-12345", expires_in=600)

        async def add_header(ctx: RequestContext) -> None:
            ctx.headers["X-Test"] = "via-client"

        client.add_before_request(add_header)

        route = respx.get(f"{TEST_BASE_URL}/products").mock(return_value=Response(200, json={}))

        await client._http.get("/products")

        assert route.calls[0].request.headers["x-test"] == "via-client"
        await client.close()
