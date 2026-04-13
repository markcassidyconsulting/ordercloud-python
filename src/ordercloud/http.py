"""Low-level HTTP client for the OrderCloud API."""

import asyncio
import logging
from typing import Any, Optional

import httpx

from .auth import TokenManager
from .config import OrderCloudConfig
from .errors import ApiError, AuthenticationError, OrderCloudError
from .middleware import AfterResponse, BeforeRequest, RequestContext, ResponseContext

__all__ = ["HttpClient"]

logger = logging.getLogger("ordercloud")

_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


class HttpClient:
    """Async HTTP client with automatic authentication and error handling.

    Wraps ``httpx.AsyncClient`` to inject bearer tokens, strip ``None``
    query parameters, raise typed exceptions on error responses, and
    optionally retry on transient failures (429, 5xx) with exponential
    backoff.

    Supports before-request and after-response middleware hooks for
    custom header injection, logging, metrics, etc.

    Args:
        config: The client configuration.
        token_manager: The token manager for acquiring bearer tokens.
    """

    def __init__(self, config: OrderCloudConfig, token_manager: TokenManager) -> None:
        self._config = config
        self._token_manager = token_manager
        self._client = httpx.AsyncClient(timeout=config.timeout)
        self._before_request: list[BeforeRequest] = []
        self._after_response: list[AfterResponse] = []

    def add_before_request(self, hook: BeforeRequest) -> None:
        """Register a hook called before each HTTP request.

        The hook receives a mutable ``RequestContext`` and can modify
        headers, params, or the JSON body before the request is sent.
        """
        self._before_request.append(hook)

    def add_after_response(self, hook: AfterResponse) -> None:
        """Register a hook called after each HTTP response.

        The hook receives a ``ResponseContext`` with the request details
        and the response.  Called on every attempt, including retries.
        """
        self._after_response.append(hook)

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

        max_attempts = 1 + self._config.max_retries

        for attempt in range(max_attempts):
            ctx = RequestContext(
                method=method,
                path=path,
                url=url,
                headers=dict(headers),
                params=dict(params) if params else None,
                json=dict(json) if json else None,
            )

            for hook in self._before_request:
                await hook(ctx)

            logger.debug("Request: %s %s", method, path)

            resp = await self._client.request(
                ctx.method,
                ctx.url,
                headers=ctx.headers,
                params=ctx.params,
                json=ctx.json,
            )

            logger.debug("Response: %s %s %d", method, path, resp.status_code)

            resp_ctx = ResponseContext(request=ctx, response=resp, attempt=attempt)
            for hook in self._after_response:
                await hook(resp_ctx)

            if resp.status_code < 400:
                return resp

            if resp.status_code in _RETRYABLE_STATUSES and attempt < max_attempts - 1:
                delay = self._retry_delay(resp, attempt)
                logger.warning(
                    "Retry %d/%d: %s %s returned %d, waiting %.1fs",
                    attempt + 1,
                    self._config.max_retries,
                    method,
                    path,
                    resp.status_code,
                    delay,
                )
                await asyncio.sleep(delay)
                continue

            self._raise_error(resp)

        # Unreachable — loop always returns or raises
        raise AssertionError("unreachable")  # pragma: no cover

    def _retry_delay(self, resp: httpx.Response, attempt: int) -> float:
        """Calculate the delay before the next retry attempt.

        Respects the ``Retry-After`` header if present, otherwise uses
        exponential backoff: ``retry_backoff * 2^attempt``.
        """
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self._config.retry_backoff * (2**attempt)

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
