from typing import Any, Optional, Union

from ..http import HttpClient
from ..models.order import Order
from ..models.shared import ListPage, Meta


class OrdersResource:
    """Operations on OrderCloud Orders."""

    def __init__(self, http: HttpClient):
        self._http = http

    async def list(
        self,
        direction: str = "Incoming",
        *,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[Order]:
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

        resp = await self._http.get(f"/orders/{direction}", **params)
        data = resp.json()
        return ListPage[Order](
            Items=[Order(**item) for item in data.get("Items", [])],
            Meta=Meta(**data.get("Meta", {})),
        )

    async def get(self, direction: str, order_id: str) -> Order:
        resp = await self._http.get(f"/orders/{direction}/{order_id}")
        return Order(**resp.json())

    async def create(self, direction: str, order: Union[Order, dict[str, Any]]) -> Order:
        body = order.model_dump(exclude_none=True) if isinstance(order, Order) else order
        resp = await self._http.post(f"/orders/{direction}", json=body)
        return Order(**resp.json())

    async def save(
        self, direction: str, order_id: str, order: Union[Order, dict[str, Any]]
    ) -> Order:
        body = order.model_dump(exclude_none=True) if isinstance(order, Order) else order
        resp = await self._http.put(f"/orders/{direction}/{order_id}", json=body)
        return Order(**resp.json())

    async def patch(self, direction: str, order_id: str, partial: dict[str, Any]) -> Order:
        resp = await self._http.patch(f"/orders/{direction}/{order_id}", json=partial)
        return Order(**resp.json())

    async def delete(self, direction: str, order_id: str) -> None:
        await self._http.delete(f"/orders/{direction}/{order_id}")

    async def submit(self, direction: str, order_id: str) -> Order:
        resp = await self._http.post(f"/orders/{direction}/{order_id}/submit")
        return Order(**resp.json())

    async def approve(self, direction: str, order_id: str, comments: str = "") -> Order:
        resp = await self._http.post(
            f"/orders/{direction}/{order_id}/approve", json={"Comments": comments}
        )
        return Order(**resp.json())

    async def cancel(self, direction: str, order_id: str) -> Order:
        resp = await self._http.post(f"/orders/{direction}/{order_id}/cancel")
        return Order(**resp.json())

    async def complete(self, direction: str, order_id: str) -> Order:
        resp = await self._http.post(f"/orders/{direction}/{order_id}/complete")
        return Order(**resp.json())
