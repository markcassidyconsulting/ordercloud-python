"""OrderCloud Catalogs API resource."""

from typing import Any, Optional, Union

from ..models.catalog import Catalog
from ..models.shared import ListPage
from .base import BaseResource

__all__ = ["CatalogsResource"]


class CatalogsResource(BaseResource):
    """Operations on OrderCloud Catalogs."""

    async def list(
        self,
        *,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[Catalog]:
        """List catalogs with optional filtering and pagination.

        Args:
            search: Free-text search term.
            sort_by: Field name to sort by (prefix with ``!`` to reverse).
            page: 1-based page number.
            page_size: Number of items per page (max 100).
            filters: Arbitrary key/value filters.

        Returns:
            A paginated list of catalogs.
        """
        params = self._build_list_params(
            search=search,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            filters=filters,
        )
        resp = await self._http.get("/catalogs", **params)
        return self._parse_list(resp.json(), Catalog)

    async def get(self, catalog_id: str) -> Catalog:
        """Retrieve a single catalog by ID.

        Args:
            catalog_id: The ID of the catalog.

        Returns:
            The requested catalog.
        """
        resp = await self._http.get(f"/catalogs/{catalog_id}")
        return Catalog(**resp.json())

    async def create(self, catalog: Union[Catalog, dict[str, Any]]) -> Catalog:
        """Create a new catalog.

        Args:
            catalog: A ``Catalog`` model or dict of catalog fields.

        Returns:
            The created catalog (with server-assigned fields populated).
        """
        resp = await self._http.post("/catalogs", json=self._serialize(catalog))
        return Catalog(**resp.json())

    async def save(self, catalog_id: str, catalog: Union[Catalog, dict[str, Any]]) -> Catalog:
        """Create or replace a catalog (PUT).

        Args:
            catalog_id: The ID of the catalog to create or replace.
            catalog: A ``Catalog`` model or dict of catalog fields.

        Returns:
            The saved catalog.
        """
        resp = await self._http.put(f"/catalogs/{catalog_id}", json=self._serialize(catalog))
        return Catalog(**resp.json())

    async def patch(self, catalog_id: str, partial: dict[str, Any]) -> Catalog:
        """Partially update a catalog (PATCH).

        Args:
            catalog_id: The ID of the catalog to update.
            partial: A dict of fields to update.

        Returns:
            The updated catalog.
        """
        resp = await self._http.patch(f"/catalogs/{catalog_id}", json=partial)
        return Catalog(**resp.json())

    async def delete(self, catalog_id: str) -> None:
        """Delete a catalog.

        Args:
            catalog_id: The ID of the catalog to delete.
        """
        await self._http.delete(f"/catalogs/{catalog_id}")
