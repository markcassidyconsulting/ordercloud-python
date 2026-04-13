from typing import Any, Optional, Union

from ..http import HttpClient
from ..models.category import Category
from ..models.shared import ListPage, Meta


class CategoriesResource:
    """Operations on OrderCloud Categories (nested under Catalogs)."""

    def __init__(self, http: HttpClient):
        self._http = http

    async def list(
        self,
        catalog_id: str,
        *,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        depth: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[Category]:
        params: dict[str, Any] = {}
        if search is not None:
            params["search"] = search
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

        resp = await self._http.get(f"/catalogs/{catalog_id}/categories", **params)
        data = resp.json()
        return ListPage[Category](
            Items=[Category(**item) for item in data.get("Items", [])],
            Meta=Meta(**data.get("Meta", {})),
        )

    async def get(self, catalog_id: str, category_id: str) -> Category:
        resp = await self._http.get(f"/catalogs/{catalog_id}/categories/{category_id}")
        return Category(**resp.json())

    async def create(self, catalog_id: str, category: Union[Category, dict[str, Any]]) -> Category:
        body = (
            category.model_dump(exclude_none=True) if isinstance(category, Category) else category
        )
        resp = await self._http.post(f"/catalogs/{catalog_id}/categories", json=body)
        return Category(**resp.json())

    async def save(
        self, catalog_id: str, category_id: str, category: Union[Category, dict[str, Any]]
    ) -> Category:
        body = (
            category.model_dump(exclude_none=True) if isinstance(category, Category) else category
        )
        resp = await self._http.put(
            f"/catalogs/{catalog_id}/categories/{category_id}", json=body
        )
        return Category(**resp.json())

    async def patch(self, catalog_id: str, category_id: str, partial: dict[str, Any]) -> Category:
        resp = await self._http.patch(
            f"/catalogs/{catalog_id}/categories/{category_id}", json=partial
        )
        return Category(**resp.json())

    async def delete(self, catalog_id: str, category_id: str) -> None:
        await self._http.delete(f"/catalogs/{catalog_id}/categories/{category_id}")
