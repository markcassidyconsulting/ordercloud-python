"""Tests for OAuth2 token management."""

from __future__ import annotations


import httpx
import respx
from httpx import Response

from ordercloud.auth import AccessToken, TokenManager
from ordercloud.config import OrderCloudConfig

from .conftest import TEST_AUTH_URL, TEST_CLIENT_ID, TEST_CLIENT_SECRET, make_token_response


# ---------------------------------------------------------------------------
# AccessToken
# ---------------------------------------------------------------------------


class TestAccessToken:
    def test_not_expired_when_fresh(self):
        token = AccessToken("tok", expires_in=600)
        assert not token.is_expired

    def test_expired_when_past_lifetime(self):
        token = AccessToken("tok", expires_in=0)
        assert token.is_expired

    def test_expired_within_safety_buffer(self):
        # 25 seconds remaining is within the 30-second buffer.
        token = AccessToken("tok", expires_in=25)
        assert token.is_expired

    def test_not_expired_outside_safety_buffer(self):
        # 35 seconds remaining is outside the 30-second buffer.
        token = AccessToken("tok", expires_in=35)
        assert not token.is_expired

    def test_stores_refresh_token(self):
        token = AccessToken("tok", expires_in=600, refresh_token="refresh-123")
        assert token.refresh_token == "refresh-123"

    def test_refresh_token_defaults_to_empty(self):
        token = AccessToken("tok", expires_in=600)
        assert token.refresh_token == ""


# ---------------------------------------------------------------------------
# TokenManager — client_credentials grant
# ---------------------------------------------------------------------------


class TestTokenManagerClientCredentials:
    @respx.mock
    async def test_acquires_token_on_first_call(self, config: OrderCloudConfig):
        respx.post(TEST_AUTH_URL).mock(
            return_value=Response(200, json=make_token_response(access_token="fresh-token"))
        )
        manager = TokenManager(config)
        async with httpx.AsyncClient() as client:
            token = await manager.get_token(client)
        assert token == "fresh-token"

    @respx.mock
    async def test_sends_correct_grant_body(self, config: OrderCloudConfig):
        route = respx.post(TEST_AUTH_URL).mock(
            return_value=Response(200, json=make_token_response())
        )
        manager = TokenManager(config)
        async with httpx.AsyncClient() as client:
            await manager.get_token(client)

        request = route.calls[0].request
        body = request.content.decode()
        assert "grant_type=client_credentials" in body
        assert f"client_id={TEST_CLIENT_ID}" in body
        assert f"client_secret={TEST_CLIENT_SECRET}" in body
        assert "scope=FullAccess" in body

    @respx.mock
    async def test_caches_token_across_calls(self, config: OrderCloudConfig):
        route = respx.post(TEST_AUTH_URL).mock(
            return_value=Response(200, json=make_token_response(access_token="cached"))
        )
        manager = TokenManager(config)
        async with httpx.AsyncClient() as client:
            t1 = await manager.get_token(client)
            t2 = await manager.get_token(client)
        assert t1 == t2 == "cached"
        assert route.call_count == 1  # Only one auth request.


# ---------------------------------------------------------------------------
# TokenManager — refresh grant
# ---------------------------------------------------------------------------


class TestTokenManagerRefresh:
    @respx.mock
    async def test_uses_refresh_token_when_expired(self, config: OrderCloudConfig):
        # First call: return token with refresh_token.
        respx.post(TEST_AUTH_URL).mock(
            side_effect=[
                Response(
                    200,
                    json=make_token_response(
                        access_token="first",
                        expires_in=0,  # Already expired.
                        refresh_token="refresh-abc",
                    ),
                ),
                Response(
                    200,
                    json=make_token_response(access_token="refreshed"),
                ),
            ]
        )
        manager = TokenManager(config)
        async with httpx.AsyncClient() as client:
            first = await manager.get_token(client)
            assert first == "first"
            # Token is expired, should refresh.
            second = await manager.get_token(client)
            assert second == "refreshed"

    @respx.mock
    async def test_refresh_sends_correct_body(self, config: OrderCloudConfig):
        route = respx.post(TEST_AUTH_URL).mock(
            side_effect=[
                Response(
                    200,
                    json=make_token_response(expires_in=0, refresh_token="ref-tok"),
                ),
                Response(200, json=make_token_response(access_token="new")),
            ]
        )
        manager = TokenManager(config)
        async with httpx.AsyncClient() as client:
            await manager.get_token(client)
            await manager.get_token(client)

        # Second call should be a refresh.
        refresh_request = route.calls[1].request
        body = refresh_request.content.decode()
        assert "grant_type=refresh_token" in body
        assert "refresh_token=ref-tok" in body

    @respx.mock
    async def test_re_authenticates_when_no_refresh_token(self, config: OrderCloudConfig):
        route = respx.post(TEST_AUTH_URL).mock(
            side_effect=[
                Response(
                    200,
                    json=make_token_response(expires_in=0, refresh_token=""),
                ),
                Response(
                    200,
                    json=make_token_response(access_token="re-authed"),
                ),
            ]
        )
        manager = TokenManager(config)
        async with httpx.AsyncClient() as client:
            await manager.get_token(client)
            token = await manager.get_token(client)
        assert token == "re-authed"
        # Both calls should be client_credentials, not refresh.
        for call in route.calls:
            assert "grant_type=client_credentials" in call.request.content.decode()


# ---------------------------------------------------------------------------
# TokenManager — password grant
# ---------------------------------------------------------------------------


class TestTokenManagerPassword:
    @respx.mock
    async def test_password_grant(self, config: OrderCloudConfig):
        route = respx.post(TEST_AUTH_URL).mock(
            return_value=Response(200, json=make_token_response(access_token="pw-token"))
        )
        manager = TokenManager(config)
        async with httpx.AsyncClient() as client:
            await manager.authenticate_password(client, "user@test.com", "s3cret!")
            token = await manager.get_token(client)

        assert token == "pw-token"
        body = route.calls[0].request.content.decode()
        assert "grant_type=password" in body
        assert "username=user%40test.com" in body
