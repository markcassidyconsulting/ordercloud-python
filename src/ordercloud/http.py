"""Low-level HTTP client for the OrderCloud API."""

from typing import Any, Optional

import httpx

from .auth import TokenManager
from .config import OrderCloudConfig
from .errors import ApiError, AuthenticationError, OrderCloudError

__all__ = ["HttpClient"]


class HttpClient:
    """Async HTTP client with automatic authentication and error handling.

    Wraps ``httpx.AsyncClient`` to inject bearer tokens, strip ``None``
    query parameters, and raise typed exceptions on error responses.

    Args:
        config: The client configuration.
        token_manager: The token manager for acquiring bearer tokens.
    """

    def __init__(self, config: OrderCloudConfig, token_manager: TokenManager) -> None:
        self._config = config
        self._token_manager = token_manager
        self._client = httpx.AsyncClient(timeout=config.timeout)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make an authenticated request to the OrderCloud API.

        Args:
            method: HTTP method (e.g. ``"GET"``, ``"POST"``).
            path: API path relative to the base URL (e.g. ``"/products"``).
            params: Query parameters (``None`` values are stripped).
            json: JSON request body.

        Returns:
            The HTTP response.

        Raises:
            AuthenticationError: On 401 or 403 responses.
            OrderCloudError: On any other 4xx/5xx response.
        """
        token = await self._token_manager.get_token(self._client)
        url = f"{self._config.base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        resp = await self._client.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json,
        )

        if resp.status_code >= 400:
            self._raise_error(resp)

        return resp

    async def get(self, path: str, **params: Any) -> httpx.Response:
        """Send a GET request."""
        return await self.request("GET", path, params=params or None)

    async def post(self, path: str, json: Optional[dict[str, Any]] = None) -> httpx.Response:
        """Send a POST request."""
        return await self.request("POST", path, json=json)

    async def put(self, path: str, json: Optional[dict[str, Any]] = None) -> httpx.Response:
        """Send a PUT request."""
        return await self.request("PUT", path, json=json)

    async def patch(self, path: str, json: Optional[dict[str, Any]] = None) -> httpx.Response:
        """Send a PATCH request."""
        return await self.request("PATCH", path, json=json)

    async def delete(self, path: str) -> httpx.Response:
        """Send a DELETE request."""
        return await self.request("DELETE", path)

    async def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        await self._client.aclose()

    @staticmethod
    def _raise_error(resp: httpx.Response) -> None:
        """Parse an error response and raise the appropriate exception."""
        try:
            body = resp.json()
            errors = [
                ApiError(
                    error_code=e.get("ErrorCode", ""),
                    message=e.get("Message", ""),
                    data=e.get("Data"),
                )
                for e in body.get("Errors", [])
            ]
        except Exception:
            errors = [ApiError(error_code="Unknown", message=resp.text)]
            body = None

        if resp.status_code in (401, 403):
            raise AuthenticationError(resp.status_code, errors, raw=body)
        raise OrderCloudError(resp.status_code, errors, raw=body)
