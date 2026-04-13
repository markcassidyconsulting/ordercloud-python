from typing import Any, Optional, Union

from ..http import HttpClient
from ..models.product import Product
from ..models.shared import ListPage, MetaWithFacets


class ProductsResource:
    """Operations on OrderCloud Products."""

    def __init__(self, http: HttpClient):
        self._http = http

    async def list(
        self,
        *,
        search: Optional[str] = None,
        search_on: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[Product]:
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
        if filters:
            params.update(filters)

        resp = await self._http.get("/products", **params)
        data = resp.json()
        return ListPage[Product](
            Items=[Product(**item) for item in data.get("Items", [])],
            Meta=MetaWithFacets(**data.get("Meta", {})),
        )

    async def get(self, product_id: str) -> Product:
        resp = await self._http.get(f"/products/{product_id}")
        return Product(**resp.json())

    async def create(self, product: Union[Product, dict[str, Any]]) -> Product:
        body = product.model_dump(exclude_none=True) if isinstance(product, Product) else product
        resp = await self._http.post("/products", json=body)
        return Product(**resp.json())

    async def save(self, product_id: str, product: Union[Product, dict[str, Any]]) -> Product:
        body = product.model_dump(exclude_none=True) if isinstance(product, Product) else product
        resp = await self._http.put(f"/products/{product_id}", json=body)
        return Product(**resp.json())

    async def patch(self, product_id: str, partial: dict[str, Any]) -> Product:
        resp = await self._http.patch(f"/products/{product_id}", json=partial)
        return Product(**resp.json())

    async def delete(self, product_id: str) -> None:
        await self._http.delete(f"/products/{product_id}")
