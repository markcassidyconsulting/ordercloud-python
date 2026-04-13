from typing import Any, Optional, Union

from ..http import HttpClient
from ..models.catalog import Catalog
from ..models.shared import ListPage, Meta


class CatalogsResource:
    """Operations on OrderCloud Catalogs."""

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
    ) -> ListPage[Catalog]:
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

        resp = await self._http.get("/catalogs", **params)
        data = resp.json()
        return ListPage[Catalog](
            Items=[Catalog(**item) for item in data.get("Items", [])],
            Meta=Meta(**data.get("Meta", {})),
        )

    async def get(self, catalog_id: str) -> Catalog:
        resp = await self._http.get(f"/catalogs/{catalog_id}")
        return Catalog(**resp.json())

    async def create(self, catalog: Union[Catalog, dict[str, Any]]) -> Catalog:
        body = catalog.model_dump(exclude_none=True) if isinstance(catalog, Catalog) else catalog
        resp = await self._http.post("/catalogs", json=body)
        return Catalog(**resp.json())

    async def save(self, catalog_id: str, catalog: Union[Catalog, dict[str, Any]]) -> Catalog:
        body = catalog.model_dump(exclude_none=True) if isinstance(catalog, Catalog) else catalog
        resp = await self._http.put(f"/catalogs/{catalog_id}", json=body)
        return Catalog(**resp.json())

    async def patch(self, catalog_id: str, partial: dict[str, Any]) -> Catalog:
        resp = await self._http.patch(f"/catalogs/{catalog_id}", json=partial)
        return Catalog(**resp.json())

    async def delete(self, catalog_id: str) -> None:
        await self._http.delete(f"/catalogs/{catalog_id}")
