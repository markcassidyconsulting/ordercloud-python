"""OrderCloud Products API resource."""

from typing import Any, Optional, Union

from ..models.product import Product
from ..models.shared import ListPage, MetaWithFacets
from .base import BaseResource

__all__ = ["ProductsResource"]


class ProductsResource(BaseResource):
    """Operations on OrderCloud Products."""

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
        """List products with optional filtering, search, and pagination.

        Args:
            search: Free-text search term.
            search_on: Comma-separated field names to search on
                (e.g. ``"Name,Description"``).
            sort_by: Field name to sort by (prefix with ``!`` to reverse).
            page: 1-based page number.
            page_size: Number of items per page (max 100).
            filters: Arbitrary key/value filters.

        Returns:
            A paginated list of products (with search facets in metadata).
        """
        params = self._build_list_params(
            search=search,
            search_on=search_on,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            filters=filters,
        )
        resp = await self._http.get("/products", **params)
        return self._parse_list(resp.json(), Product, meta_cls=MetaWithFacets)

    async def get(self, product_id: str) -> Product:
        """Retrieve a single product by ID.

        Args:
            product_id: The ID of the product.

        Returns:
            The requested product.
        """
        resp = await self._http.get(f"/products/{product_id}")
        return Product(**resp.json())

    async def create(self, product: Union[Product, dict[str, Any]]) -> Product:
        """Create a new product.

        Args:
            product: A ``Product`` model or dict of product fields.

        Returns:
            The created product (with server-assigned fields populated).
        """
        resp = await self._http.post("/products", json=self._serialize(product))
        return Product(**resp.json())

    async def save(self, product_id: str, product: Union[Product, dict[str, Any]]) -> Product:
        """Create or replace a product (PUT).

        Args:
            product_id: The ID of the product to create or replace.
            product: A ``Product`` model or dict of product fields.

        Returns:
            The saved product.
        """
        resp = await self._http.put(f"/products/{product_id}", json=self._serialize(product))
        return Product(**resp.json())

    async def patch(self, product_id: str, partial: dict[str, Any]) -> Product:
        """Partially update a product (PATCH).

        Args:
            product_id: The ID of the product to update.
            partial: A dict of fields to update.

        Returns:
            The updated product.
        """
        resp = await self._http.patch(f"/products/{product_id}", json=partial)
        return Product(**resp.json())

    async def delete(self, product_id: str) -> None:
        """Delete a product.

        Args:
            product_id: The ID of the product to delete.
        """
        await self._http.delete(f"/products/{product_id}")
