from typing import Any, Optional, Union

from ..http import HttpClient
from ..models.line_item import LineItem
from ..models.shared import ListPage, Meta


class LineItemsResource:
    """Operations on OrderCloud Line Items (nested under Orders)."""

    def __init__(self, http: HttpClient):
        self._http = http

    def _base(self, direction: str, order_id: str) -> str:
        return f"/orders/{direction}/{order_id}/lineitems"

    async def list(
        self,
        direction: str,
        order_id: str,
        *,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[LineItem]:
        params: dict[str, Any] = {}
        if search is not None:
            params["search"] = search
        if sort_by is not None:
            params["sortBy"] = sort_by
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        if filters:
            params.update(filters)

        resp = await self._http.get(self._base(direction, order_id), **params)
        data = resp.json()
        return ListPage[LineItem](
            Items=[LineItem(**item) for item in data.get("Items", [])],
            Meta=Meta(**data.get("Meta", {})),
        )

    async def get(self, direction: str, order_id: str, line_item_id: str) -> LineItem:
        resp = await self._http.get(f"{self._base(direction, order_id)}/{line_item_id}")
        return LineItem(**resp.json())

    async def create(
        self, direction: str, order_id: str, line_item: Union[LineItem, dict[str, Any]]
    ) -> LineItem:
        body = (
            line_item.model_dump(exclude_none=True)
            if isinstance(line_item, LineItem)
            else line_item
        )
        resp = await self._http.post(self._base(direction, order_id), json=body)
        return LineItem(**resp.json())

    async def save(
        self,
        direction: str,
        order_id: str,
        line_item_id: str,
        line_item: Union[LineItem, dict[str, Any]],
    ) -> LineItem:
        body = (
            line_item.model_dump(exclude_none=True)
            if isinstance(line_item, LineItem)
            else line_item
        )
        resp = await self._http.put(
            f"{self._base(direction, order_id)}/{line_item_id}", json=body
        )
        return LineItem(**resp.json())

    async def patch(
        self, direction: str, order_id: str, line_item_id: str, partial: dict[str, Any]
    ) -> LineItem:
        resp = await self._http.patch(
            f"{self._base(direction, order_id)}/{line_item_id}", json=partial
        )
        return LineItem(**resp.json())

    async def delete(self, direction: str, order_id: str, line_item_id: str) -> None:
        await self._http.delete(f"{self._base(direction, order_id)}/{line_item_id}")
