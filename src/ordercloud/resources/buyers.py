"""OrderCloud Buyers API resource."""

from typing import Any, Optional, Union

from ..models.buyer import Buyer
from ..models.shared import ListPage
from .base import BaseResource

__all__ = ["BuyersResource"]


class BuyersResource(BaseResource):
    """Operations on OrderCloud Buyers."""

    async def list(
        self,
        *,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[Buyer]:
        """List buyers with optional filtering and pagination.

        Args:
            search: Free-text search term.
            sort_by: Field name to sort by (prefix with ``!`` to reverse).
            page: 1-based page number.
            page_size: Number of items per page (max 100).
            filters: Arbitrary key/value filters.

        Returns:
            A paginated list of buyers.
        """
        params = self._build_list_params(
            search=search,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            filters=filters,
        )
        resp = await self._http.get("/buyers", **params)
        return self._parse_list(resp.json(), Buyer)

    async def get(self, buyer_id: str) -> Buyer:
        """Retrieve a single buyer by ID.

        Args:
            buyer_id: The ID of the buyer.

        Returns:
            The requested buyer.
        """
        resp = await self._http.get(f"/buyers/{buyer_id}")
        return Buyer(**resp.json())

    async def create(self, buyer: Union[Buyer, dict[str, Any]]) -> Buyer:
        """Create a new buyer.

        Args:
            buyer: A ``Buyer`` model or dict of buyer fields.

        Returns:
            The created buyer (with server-assigned fields populated).
        """
        resp = await self._http.post("/buyers", json=self._serialize(buyer))
        return Buyer(**resp.json())

    async def save(self, buyer_id: str, buyer: Union[Buyer, dict[str, Any]]) -> Buyer:
        """Create or replace a buyer (PUT).

        Args:
            buyer_id: The ID of the buyer to create or replace.
            buyer: A ``Buyer`` model or dict of buyer fields.

        Returns:
            The saved buyer.
        """
        resp = await self._http.put(f"/buyers/{buyer_id}", json=self._serialize(buyer))
        return Buyer(**resp.json())

    async def patch(self, buyer_id: str, partial: dict[str, Any]) -> Buyer:
        """Partially update a buyer (PATCH).

        Args:
            buyer_id: The ID of the buyer to update.
            partial: A dict of fields to update.

        Returns:
            The updated buyer.
        """
        resp = await self._http.patch(f"/buyers/{buyer_id}", json=partial)
        return Buyer(**resp.json())

    async def delete(self, buyer_id: str) -> None:
        """Delete a buyer.

        Args:
            buyer_id: The ID of the buyer to delete.
        """
        await self._http.delete(f"/buyers/{buyer_id}")
