import time
from typing import Optional

import httpx

from .config import OrderCloudConfig


class AccessToken:
    """An OAuth2 access token with expiry tracking."""

    def __init__(self, access_token: str, expires_in: int, refresh_token: str = ""):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._expires_at = time.time() + expires_in

    @property
    def is_expired(self) -> bool:
        return time.time() >= self._expires_at - 30  # 30s buffer


class TokenManager:
    """Handles OAuth2 token acquisition and automatic refresh."""

    def __init__(self, config: OrderCloudConfig):
        self._config = config
        self._token: Optional[AccessToken] = None

    async def get_token(self, client: httpx.AsyncClient) -> str:
        """Return a valid access token, refreshing if needed."""
        if self._token is None or self._token.is_expired:
            if self._token and self._token.refresh_token:
                await self._refresh(client)
            else:
                await self._authenticate(client)
        return self._token.access_token

    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        """Authenticate via client_credentials grant."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "scope": " ".join(self._config.scopes),
        }
        resp = await client.post(self._config.auth_url, data=data)
        resp.raise_for_status()
        body = resp.json()
        self._token = AccessToken(
            access_token=body["access_token"],
            expires_in=body.get("expires_in", 600),
            refresh_token=body.get("refresh_token", ""),
        )

    async def _refresh(self, client: httpx.AsyncClient) -> None:
        """Refresh an existing token."""
        data = {
            "grant_type": "refresh_token",
            "client_id": self._config.client_id,
            "refresh_token": self._token.refresh_token,
        }
        resp = await client.post(self._config.auth_url, data=data)
        resp.raise_for_status()
        body = resp.json()
        self._token = AccessToken(
            access_token=body["access_token"],
            expires_in=body.get("expires_in", 600),
            refresh_token=body.get("refresh_token", ""),
        )

    async def authenticate_password(
        self, client: httpx.AsyncClient, username: str, password: str
    ) -> None:
        """Authenticate via password grant."""
        data = {
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
        body = resp.json()
        self._token = AccessToken(
            access_token=body["access_token"],
            expires_in=body.get("expires_in", 600),
            refresh_token=body.get("refresh_token", ""),
        )
