"""Tests for the HTTP client and error handling."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ordercloud.errors import AuthenticationError, OrderCloudError
from ordercloud.http import HttpClient

from .conftest import TEST_BASE_URL


# ---------------------------------------------------------------------------
# Request building
# ---------------------------------------------------------------------------


class TestRequestBuilding:
    @respx.mock
    async def test_get_sends_bearer_token(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(200, json={})
        )
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
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(200, json={})
        )
        await http_client.get("/products", search="widget", page=1, pageSize=20)
        url = route.calls[0].request.url
        assert "search=widget" in str(url)
        assert "page=1" in str(url)
        assert "pageSize=20" in str(url)

    @respx.mock
    async def test_get_strips_none_params(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(200, json={})
        )
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
        route = respx.delete(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(204)
        )
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
        respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(400, json=raw)
        )
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
