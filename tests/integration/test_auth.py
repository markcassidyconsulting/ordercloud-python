"""Integration tests: OAuth2 authentication flow.

Verifies that client_credentials grant works against the live sandbox,
that tokens are cached across requests, and that the bearer token has
a reasonable format.
"""

from __future__ import annotations

import pytest

from ordercloud import OrderCloudClient, OrderCloudConfig


class TestAuth:
    """Verify authentication against the live sandbox."""

    async def test_client_credentials_grant(self, async_client: OrderCloudClient) -> None:
        """A simple API call succeeds, proving client_credentials auth works."""
        page = await async_client.products.list(page_size=1)
        # If auth failed, we'd never get here — an exception would be raised.
        assert page.meta.page >= 1
        assert page.meta.page_size >= 1

    async def test_token_caching(self, async_client: OrderCloudClient) -> None:
        """The same bearer token is reused across consecutive requests."""
        tokens: list[str] = []

        async def capture_token(ctx: object) -> None:
            tokens.append(ctx.headers.get("Authorization", ""))  # type: ignore[attr-defined]

        async_client.add_before_request(capture_token)  # type: ignore[arg-type]

        await async_client.products.list(page_size=1)
        await async_client.products.list(page_size=1)

        assert len(tokens) == 2
        assert tokens[0] == tokens[1], "Token should be cached, not re-acquired"
        assert tokens[0].startswith("Bearer ")

    async def test_bearer_token_format(self, async_client: OrderCloudClient) -> None:
        """The Authorization header contains a substantial bearer token."""
        token_header: list[str] = []

        async def capture(ctx: object) -> None:
            token_header.append(ctx.headers.get("Authorization", ""))  # type: ignore[attr-defined]

        async_client.add_before_request(capture)  # type: ignore[arg-type]
        await async_client.products.list(page_size=1)

        assert len(token_header) == 1
        assert token_header[0].startswith("Bearer ")
        bearer = token_header[0][len("Bearer ") :]
        assert len(bearer) > 20, "Token should be a substantial string"

    async def test_bad_credentials_fail(self, oc_config: OrderCloudConfig) -> None:
        """A client with invalid credentials fails when making a request."""
        bad_config = OrderCloudConfig(
            client_id="invalid-client-id-00000000",
            client_secret="invalid-secret",
            base_url=oc_config.base_url,
            auth_url=oc_config.auth_url,
        )
        async with OrderCloudClient(bad_config) as client:
            with pytest.raises(Exception):
                await client.products.list(page_size=1)
