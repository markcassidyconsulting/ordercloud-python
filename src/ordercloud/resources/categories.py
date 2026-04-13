"""OrderCloud Categories API resource (nested under Catalogs)."""

from typing import Any, Optional, Union

from ..models.category import Category
from ..models.shared import ListPage
from .base import BaseResource

__all__ = ["CategoriesResource"]


class CategoriesResource(BaseResource):
    """Operations on OrderCloud Categories (nested under Catalogs)."""

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
        """List categories within a catalog.

        Args:
            catalog_id: The ID of the parent catalog.
            search: Free-text search term.
            sort_by: Field name to sort by (prefix with ``!`` to reverse).
            page: 1-based page number.
            page_size: Number of items per page (max 100).
            depth: Category tree depth to return (e.g. ``"all"``).
            filters: Arbitrary key/value filters.

        Returns:
            A paginated list of categories.
        """
        params = self._build_list_params(
            search=search,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            depth=depth,
            filters=filters,
        )
        resp = await self._http.get(f"/catalogs/{catalog_id}/categories", **params)
        return self._parse_list(resp.json(), Category)

    async def get(self, catalog_id: str, category_id: str) -> Category:
        """Retrieve a single category.

        Args:
            catalog_id: The ID of the parent catalog.
            category_id: The ID of the category.

        Returns:
            The requested category.
        """
        resp = await self._http.get(f"/catalogs/{catalog_id}/categories/{category_id}")
        return Category(**resp.json())

    async def create(self, catalog_id: str, category: Union[Category, dict[str, Any]]) -> Category:
        """Create a new category within a catalog.

        Args:
            catalog_id: The ID of the parent catalog.
            category: A ``Category`` model or dict of category fields.

        Returns:
            The created category (with server-assigned fields populated).
        """
        resp = await self._http.post(
            f"/catalogs/{catalog_id}/categories",
            json=self._serialize(category),
        )
        return Category(**resp.json())

    async def save(
        self, catalog_id: str, category_id: str, category: Union[Category, dict[str, Any]]
    ) -> Category:
        """Create or replace a category (PUT).

        Args:
            catalog_id: The ID of the parent catalog.
            category_id: The ID of the category to create or replace.
            category: A ``Category`` model or dict of category fields.

        Returns:
            The saved category.
        """
        resp = await self._http.put(
            f"/catalogs/{catalog_id}/categories/{category_id}",
            json=self._serialize(category),
        )
        return Category(**resp.json())

    async def patch(self, catalog_id: str, category_id: str, partial: dict[str, Any]) -> Category:
        """Partially update a category (PATCH).

        Args:
            catalog_id: The ID of the parent catalog.
            category_id: The ID of the category to update.
            partial: A dict of fields to update.

        Returns:
            The updated category.
        """
        resp = await self._http.patch(
            f"/catalogs/{catalog_id}/categories/{category_id}",
            json=partial,
        )
        return Category(**resp.json())

    async def delete(self, catalog_id: str, category_id: str) -> None:
        """Delete a category.

        Args:
            catalog_id: The ID of the parent catalog.
            category_id: The ID of the category to delete.
        """
        await self._http.delete(f"/catalogs/{catalog_id}/categories/{category_id}")
