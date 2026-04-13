"""OAuth2 token management for OrderCloud API authentication."""

import asyncio
import time
from typing import Any, Optional

import httpx

from .config import OrderCloudConfig

__all__ = ["AccessToken", "TokenManager"]


class AccessToken:
    """An OAuth2 access token with expiry tracking.

    Stores the token string, optional refresh token, and calculates an
    absolute expiry timestamp with a 30-second safety buffer.

    Args:
        access_token: The bearer token string.
        expires_in: Token lifetime in seconds (from the OAuth2 response).
        refresh_token: Optional refresh token for token renewal.
    """

    def __init__(self, access_token: str, expires_in: int, refresh_token: str = "") -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._expires_at = time.time() + expires_in

    @property
    def is_expired(self) -> bool:
        """Whether the token has expired (with a 30-second safety buffer)."""
        return time.time() >= self._expires_at - 30


class TokenManager:
    """Handles OAuth2 token acquisition and automatic refresh.

    Supports ``client_credentials`` and ``password`` grant types.
    Tokens are cached and automatically refreshed when expired.
    Thread-safe under concurrent async access via an internal lock.

    Args:
        config: The client configuration containing credentials and URLs.
    """

    def __init__(self, config: OrderCloudConfig) -> None:
        self._config = config
        self._token: Optional[AccessToken] = None
        self._lock = asyncio.Lock()

    @staticmethod
    def _parse_token_response(body: dict[str, Any]) -> AccessToken:
        """Parse an OAuth2 token response into an ``AccessToken``."""
        return AccessToken(
            access_token=body["access_token"],
            expires_in=body.get("expires_in", 600),
            refresh_token=body.get("refresh_token", ""),
        )

    async def get_token(self, client: httpx.AsyncClient) -> str:
        """Return a valid access token, refreshing if needed.

        If a refresh token is available, attempts refresh first.  On
        failure, clears the stale token and falls back to a full
        ``client_credentials`` authentication.

        Args:
            client: The HTTP client to use for token requests.

        Returns:
            A valid bearer token string.
        """
        async with self._lock:
            if self._token is None or self._token.is_expired:
                if self._token and self._token.refresh_token:
                    try:
                        await self._refresh(client)
                    except httpx.HTTPStatusError:
                        self._token = None
                        await self._authenticate(client)
                else:
                    await self._authenticate(client)
            assert self._token is not None
            return self._token.access_token

    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        """Authenticate via the ``client_credentials`` grant type."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "scope": " ".join(self._config.scopes),
        }
        resp = await client.post(self._config.auth_url, data=data)
        resp.raise_for_status()
        self._token = self._parse_token_response(resp.json())

    async def _refresh(self, client: httpx.AsyncClient) -> None:
        """Refresh an existing token using the ``refresh_token`` grant type."""
        assert self._token is not None
        data = {
            "grant_type": "refresh_token",
            "client_id": self._config.client_id,
            "refresh_token": self._token.refresh_token,
        }
        resp = await client.post(self._config.auth_url, data=data)
        resp.raise_for_status()
        self._token = self._parse_token_response(resp.json())

    async def authenticate_password(
        self, client: httpx.AsyncClient, username: str, password: str
    ) -> None:
        """Authenticate via the ``password`` grant type.

        Args:
            client: The HTTP client to use for the token request.
            username: The buyer user's username.
            password: The buyer user's password.
        """
        data: dict[str, str] = {
            "grant_type": "password",
            "client_id": self._config.client_id,
            "username": username,
            "password": password,
            "scope": " ".join(self._config.scopes),
        }
        if self._config.client_secret:
            data["client_secret"] = self._config.client_secret
        resp = await client.post(self._config.auth_url, data=data)
        resp.raise_for_status()
        self._token = self._parse_token_response(resp.json())
