"""Base resource class with shared helpers for OrderCloud API resources."""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

from ..http import HttpClient
from ..models.shared import ListPage, Meta

T = TypeVar("T", bound=BaseModel)

__all__ = ["BaseResource", "paginate"]


async def paginate(
    list_method: Callable[..., Awaitable[ListPage[T]]],
    *args: Any,
    page_size: int = 100,
    **kwargs: Any,
) -> AsyncIterator[T]:
    """Auto-paginate any list endpoint, yielding individual items.

    Calls ``list_method`` repeatedly, incrementing the page number until
    all pages have been fetched.  Yields items one at a time.

    Args:
        list_method: A bound list method (e.g. ``client.products.list``).
        *args: Positional arguments forwarded to the list method.
        page_size: Items per page (default 100, the API maximum).
        **kwargs: Keyword arguments forwarded to the list method.

    Yields:
        Individual items across all pages.

    Example::

        from ordercloud.resources import paginate

        async for product in paginate(client.products.list, search="widget"):
            print(product.Name)
    """
    page = 1
    kwargs["page_size"] = page_size
    while True:
        kwargs["page"] = page
        result = await list_method(*args, **kwargs)
        for item in result.Items:
            yield item
        if page >= result.Meta.TotalPages:
            break
        page += 1


class BaseResource:
    """Base class for OrderCloud API resource clients.

    Provides shared infrastructure used by all resource implementations:
    HTTP client storage, list-parameter building, response parsing,
    and model serialisation.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    @staticmethod
    def _build_list_params(
        *,
        search: Optional[str] = None,
        search_on: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        depth: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Build query parameters for a list endpoint.

        Maps snake_case Python parameter names to the camelCase names
        expected by the OrderCloud API.  Only non-None values are included.

        Args:
            search: Free-text search term.
            search_on: Comma-separated field names to search on.
            sort_by: Field name to sort by (prefix with ``!`` to reverse).
            page: 1-based page number.
            page_size: Number of items per page (max 100).
            depth: Category tree depth (categories only).
            filters: Arbitrary key/value filters merged into the params.

        Returns:
            A dict of query parameters ready to pass to the HTTP client.
        """
        params: dict[str, Any] = {}
        if search is not None:
            params["search"] = search
        if search_on is not None:
            params["searchOn"] = search_on
        if sort_by is not None:
            params["sortBy"] = sort_by
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        if depth is not None:
            params["depth"] = depth
        if filters:
            params.update(filters)
        return params

    @staticmethod
    def _parse_list(
        data: dict[str, Any], model_cls: type[T], meta_cls: type[Meta] = Meta
    ) -> ListPage[T]:
        """Parse a raw JSON dict into a typed ``ListPage``.

        Args:
            data: Decoded JSON body from a list endpoint response.
            model_cls: The Pydantic model class for individual items.
            meta_cls: The metadata class (``Meta`` or ``MetaWithFacets``).

        Returns:
            A ``ListPage`` containing parsed items and pagination metadata.
        """
        return ListPage[model_cls](  # type: ignore[valid-type]
            Items=[model_cls.model_validate(item) for item in data.get("Items", [])],
            Meta=meta_cls.model_validate(data.get("Meta", {})),
        )

    @staticmethod
    def _serialize(model: Any) -> dict[str, Any]:
        """Serialise a Pydantic model or plain dict for an API request body.

        Accepts either a Pydantic ``BaseModel`` instance (serialised with
        ``exclude_none=True``) or a raw ``dict`` (passed through unchanged).

        Args:
            model: A Pydantic model instance or a dict.

        Returns:
            A JSON-serialisable dict.
        """
        if isinstance(model, BaseModel):
            return model.model_dump(exclude_none=True)
        return model
