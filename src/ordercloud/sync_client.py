"""Synchronous wrapper around the async OrderCloud client."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Iterator
from typing import Any, TypeVar

from .config import OrderCloudConfig
from .middleware import AfterResponse, BeforeRequest
from .resources.base import BaseResource

T = TypeVar("T")

__all__ = ["SyncOrderCloudClient", "paginate_sync"]


class _SyncProxy:
    """Wraps an async resource, making all async methods synchronous.

    When an attribute is accessed that is a coroutine function, it is
    wrapped so that calling it runs the coroutine to completion on the
    client's event loop and returns the result directly.
    """

    def __init__(self, async_resource: BaseResource, runner: Any) -> None:
        self._async = async_resource
        self._run = runner

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._async, name)
        if asyncio.iscoroutinefunction(attr):

            @functools.wraps(attr)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return self._run(attr(*args, **kwargs))

            return sync_wrapper
        return attr


class SyncOrderCloudClient:
    """Synchronous client for the OrderCloud API.

    A thin wrapper around ``OrderCloudClient`` that manages its own
    event loop internally.  All resource methods are available as
    regular (non-async) calls.

    Usage::

        with SyncOrderCloudClient.create(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET",
        ) as client:
            products = client.products.list()
    """

    def __init__(self, config: OrderCloudConfig) -> None:
        # Import here to avoid circular import at module level.
        from .client import OrderCloudClient

        self._loop = asyncio.new_event_loop()
        self._async_client = OrderCloudClient(config)

        # Auto-wrap all resource attributes with sync proxies.
        for name, value in vars(self._async_client).items():
            if isinstance(value, BaseResource):
                object.__setattr__(self, name, _SyncProxy(value, self._run))

    @classmethod
    def create(
        cls,
        *,
        client_id: str,
        client_secret: str,
        base_url: str = "https://api.ordercloud.io/v1",
        auth_url: str = "https://auth.ordercloud.io/oauth/token",
        scopes: list[str] | None = None,
        timeout: float = 30.0,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
    ) -> SyncOrderCloudClient:
        """Create a client from individual parameters.

        Args:
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            base_url: API base URL (default: US production).
            auth_url: OAuth2 token endpoint.
            scopes: Requested scopes (default: ``["FullAccess"]``).
            timeout: HTTP request timeout in seconds.
            max_retries: Maximum retries on 429/5xx (0 = disabled).
            retry_backoff: Base delay for exponential backoff.

        Returns:
            A configured ``SyncOrderCloudClient`` instance.
        """
        config = OrderCloudConfig(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            auth_url=auth_url,
            scopes=scopes or ["FullAccess"],
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )
        return cls(config)

    def _run(self, coro: Any) -> Any:
        """Run a coroutine to completion on the internal event loop."""
        return self._loop.run_until_complete(coro)

    def add_before_request(self, hook: BeforeRequest) -> None:
        """Register a hook called before each HTTP request."""
        self._async_client.add_before_request(hook)

    def add_after_response(self, hook: AfterResponse) -> None:
        """Register a hook called after each HTTP response."""
        self._async_client.add_after_response(hook)

    def close(self) -> None:
        """Close the underlying HTTP client and event loop."""
        self._run(self._async_client.close())
        self._loop.close()

    def __enter__(self) -> SyncOrderCloudClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def paginate_sync(
    list_method: Any,
    *args: Any,
    page_size: int = 100,
    **kwargs: Any,
) -> Iterator[Any]:
    """Auto-paginate any sync list method, yielding individual items.

    Works with the sync proxy methods on ``SyncOrderCloudClient``.

    Args:
        list_method: A bound sync list method (e.g. ``client.products.list``).
        *args: Positional arguments forwarded to the list method.
        page_size: Items per page (default 100, the API maximum).
        **kwargs: Keyword arguments forwarded to the list method.

    Yields:
        Individual items across all pages.

    Example::

        from ordercloud.sync_client import SyncOrderCloudClient, paginate_sync

        with SyncOrderCloudClient.create(...) as client:
            for product in paginate_sync(client.products.list, search="widget"):
                print(product.Name)
    """
    page = 1
    kwargs["page_size"] = page_size
    while True:
        kwargs["page"] = page
        result = list_method(*args, **kwargs)
        yield from result.Items
        if page >= result.Meta.TotalPages:
            break
        page += 1
