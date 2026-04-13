"""Shared fixtures for OrderCloud SDK tests."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ordercloud.auth import AccessToken, TokenManager
from ordercloud.config import OrderCloudConfig
from ordercloud.http import HttpClient


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEST_BASE_URL = "https://test-api.ordercloud.io/v1"
TEST_AUTH_URL = "https://test-auth.ordercloud.io/oauth/token"
TEST_CLIENT_ID = "test-client-id"
TEST_CLIENT_SECRET = "test-client-secret"


@pytest.fixture
def config() -> OrderCloudConfig:
    """A test configuration pointing at mock URLs."""
    return OrderCloudConfig(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
        base_url=TEST_BASE_URL,
        auth_url=TEST_AUTH_URL,
        scopes=["FullAccess"],
        timeout=5.0,
    )


# ---------------------------------------------------------------------------
# Auth mocking
# ---------------------------------------------------------------------------

TOKEN_RESPONSE = {
    "access_token": "mock-token-12345",
    "token_type": "bearer",
    "expires_in": 600,
    "refresh_token": "",
}


def make_token_response(
    *,
    access_token: str = "mock-token-12345",
    expires_in: int = 600,
    refresh_token: str = "",
) -> dict:
    """Build a synthetic OAuth2 token response."""
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
    }


@pytest.fixture
def mock_auth(config: OrderCloudConfig) -> respx.Router:
    """A respx router with a mocked auth endpoint.

    Returns the router so tests can inspect calls or override responses.
    """
    router = respx.Router(assert_all_called=False)
    router.post(config.auth_url).mock(
        return_value=Response(200, json=TOKEN_RESPONSE)
    )
    return router


# ---------------------------------------------------------------------------
# HTTP client with mocked auth
# ---------------------------------------------------------------------------


@pytest.fixture
def retry_config() -> OrderCloudConfig:
    """A test configuration with retries enabled."""
    return OrderCloudConfig(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
        base_url=TEST_BASE_URL,
        auth_url=TEST_AUTH_URL,
        scopes=["FullAccess"],
        timeout=5.0,
        max_retries=3,
        retry_backoff=0.0,  # No actual delay in tests
    )


@pytest.fixture
async def retry_http_client(
    retry_config: OrderCloudConfig, mock_auth: respx.Router
) -> HttpClient:
    """An HttpClient with retries enabled and zero backoff for fast tests."""
    token_manager = TokenManager(retry_config)
    client = HttpClient(retry_config, token_manager)
    token_manager._token = AccessToken("mock-token-12345", expires_in=600)
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def http_client(config: OrderCloudConfig, mock_auth: respx.Router) -> HttpClient:
    """An HttpClient wired to a mocked auth endpoint.

    The respx router is activated for the duration of the test.  Tests
    should add their own API endpoint mocks via the ``mock_api`` fixture
    or by using ``respx.mock`` directly.
    """
    token_manager = TokenManager(config)
    client = HttpClient(config, token_manager)
    # Pre-populate a valid token so tests don't need to mock auth
    # unless they specifically want to test auth flows.
    token_manager._token = AccessToken("mock-token-12345", expires_in=600)
    try:
        yield client
    finally:
        await client.close()
