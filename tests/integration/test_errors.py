"""Integration tests: error handling against real API responses.

Verifies that the SDK parses error responses correctly and raises
the appropriate exception types with structured error information.
"""

from __future__ import annotations

import pytest

from ordercloud import OrderCloudClient, OrderCloudConfig, OrderCloudError


class TestErrorHandling:
    """Verify error parsing against real 400/404 responses."""

    async def test_404_raises_ordercloud_error(self, async_client: OrderCloudClient) -> None:
        """Getting a nonexistent resource raises OrderCloudError with 404."""
        with pytest.raises(OrderCloudError) as exc_info:
            await async_client.products.get("nonexistent-product-xyz-99999")
        assert exc_info.value.status_code == 404

    async def test_error_has_structured_api_errors(self, async_client: OrderCloudClient) -> None:
        """The exception includes structured ApiError objects from the response."""
        with pytest.raises(OrderCloudError) as exc_info:
            await async_client.products.get("nonexistent-product-xyz-99999")

        err = exc_info.value
        assert len(err.errors) >= 1
        assert err.errors[0].error_code != ""
        assert err.errors[0].message != ""

    async def test_error_str_includes_status(self, async_client: OrderCloudClient) -> None:
        """The exception string includes the HTTP status code."""
        with pytest.raises(OrderCloudError) as exc_info:
            await async_client.products.get("nonexistent-product-xyz-99999")
        assert "404" in str(exc_info.value)

    async def test_error_raw_body(self, async_client: OrderCloudClient) -> None:
        """The exception preserves the raw response body for debugging."""
        with pytest.raises(OrderCloudError) as exc_info:
            await async_client.products.get("nonexistent-product-xyz-99999")

        err = exc_info.value
        assert err.raw is not None
        assert "Errors" in err.raw

    async def test_bad_credentials_fail_on_first_request(self, oc_config: OrderCloudConfig) -> None:
        """A client with invalid credentials fails when making its first request."""
        bad_config = OrderCloudConfig(
            client_id="00000000-0000-0000-0000-000000000000",
            client_secret="totally-invalid-secret",
            base_url=oc_config.base_url,
            auth_url=oc_config.auth_url,
        )
        async with OrderCloudClient(bad_config) as client:
            # The auth endpoint returns an error; the SDK should not silently succeed.
            with pytest.raises(Exception):
                await client.products.list(page_size=1)
