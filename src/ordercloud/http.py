from typing import Any, Optional, TypeVar

import httpx
from pydantic import BaseModel

from .auth import TokenManager
from .config import OrderCloudConfig
from .errors import ApiError, AuthenticationError, OrderCloudError

T = TypeVar("T", bound=BaseModel)


class HttpClient:
    """Low-level HTTP client with auth handling and typed responses."""

    def __init__(self, config: OrderCloudConfig, token_manager: TokenManager):
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
        """Make an authenticated request to the OrderCloud API."""
        token = await self._token_manager.get_token(self._client)
        url = f"{self._config.base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        # Strip None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        resp = await self._client.request(
            method, url, headers=headers, params=params, json=json
        )

        if resp.status_code >= 400:
            self._raise_error(resp)

        return resp

    async def get(self, path: str, **params: Any) -> httpx.Response:
        return await self.request("GET", path, params=params or None)

    async def post(self, path: str, json: Optional[dict[str, Any]] = None) -> httpx.Response:
        return await self.request("POST", path, json=json)

    async def put(self, path: str, json: Optional[dict[str, Any]] = None) -> httpx.Response:
        return await self.request("PUT", path, json=json)

    async def patch(self, path: str, json: Optional[dict[str, Any]] = None) -> httpx.Response:
        return await self.request("PATCH", path, json=json)

    async def delete(self, path: str) -> httpx.Response:
        return await self.request("DELETE", path)

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _raise_error(resp: httpx.Response) -> None:
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
