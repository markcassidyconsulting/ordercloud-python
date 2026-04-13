from typing import Any, Optional, Union

from ..http import HttpClient
from ..models.buyer import Buyer
from ..models.shared import ListPage, Meta


class BuyersResource:
    """Operations on OrderCloud Buyers."""

    def __init__(self, http: HttpClient):
        self._http = http

    async def list(
        self,
        *,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[Buyer]:
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

        resp = await self._http.get("/buyers", **params)
        data = resp.json()
        return ListPage[Buyer](
            Items=[Buyer(**item) for item in data.get("Items", [])],
            Meta=Meta(**data.get("Meta", {})),
        )

    async def get(self, buyer_id: str) -> Buyer:
        resp = await self._http.get(f"/buyers/{buyer_id}")
        return Buyer(**resp.json())

    async def create(self, buyer: Union[Buyer, dict[str, Any]]) -> Buyer:
        body = buyer.model_dump(exclude_none=True) if isinstance(buyer, Buyer) else buyer
        resp = await self._http.post("/buyers", json=body)
        return Buyer(**resp.json())

    async def save(self, buyer_id: str, buyer: Union[Buyer, dict[str, Any]]) -> Buyer:
        body = buyer.model_dump(exclude_none=True) if isinstance(buyer, Buyer) else buyer
        resp = await self._http.put(f"/buyers/{buyer_id}", json=body)
        return Buyer(**resp.json())

    async def patch(self, buyer_id: str, partial: dict[str, Any]) -> Buyer:
        resp = await self._http.patch(f"/buyers/{buyer_id}", json=partial)
        return Buyer(**resp.json())

    async def delete(self, buyer_id: str) -> None:
        await self._http.delete(f"/buyers/{buyer_id}")
