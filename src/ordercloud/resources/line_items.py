"""OrderCloud Line Items API resource (nested under Orders)."""

from typing import Any, Optional, Union

from ..models.line_item import LineItem
from ..models.order import OrderDirection
from ..models.shared import ListPage
from .base import BaseResource

__all__ = ["LineItemsResource"]


class LineItemsResource(BaseResource):
    """Operations on OrderCloud Line Items (nested under Orders)."""

    @staticmethod
    def _base_path(direction: OrderDirection, order_id: str) -> str:
        """Build the base URL path for line items under an order."""
        return f"/orders/{direction}/{order_id}/lineitems"

    async def list(
        self,
        direction: OrderDirection,
        order_id: str,
        *,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[LineItem]:
        """List line items for an order.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the parent order.
            search: Free-text search term.
            sort_by: Field name to sort by (prefix with ``!`` to reverse).
            page: 1-based page number.
            page_size: Number of items per page (max 100).
            filters: Arbitrary key/value filters.

        Returns:
            A paginated list of line items.
        """
        params = self._build_list_params(
            search=search,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            filters=filters,
        )
        resp = await self._http.get(self._base_path(direction, order_id), **params)
        return self._parse_list(resp.json(), LineItem)

    async def get(self, direction: OrderDirection, order_id: str, line_item_id: str) -> LineItem:
        """Retrieve a single line item.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the parent order.
            line_item_id: The ID of the line item.

        Returns:
            The requested line item.
        """
        resp = await self._http.get(
            f"{self._base_path(direction, order_id)}/{line_item_id}",
        )
        return LineItem(**resp.json())

    async def create(
        self, direction: OrderDirection, order_id: str, line_item: Union[LineItem, dict[str, Any]]
    ) -> LineItem:
        """Create a new line item on an order.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the parent order.
            line_item: A ``LineItem`` model or dict of line item fields.

        Returns:
            The created line item (with server-assigned fields populated).
        """
        resp = await self._http.post(
            self._base_path(direction, order_id),
            json=self._serialize(line_item),
        )
        return LineItem(**resp.json())

    async def save(
        self,
        direction: OrderDirection,
        order_id: str,
        line_item_id: str,
        line_item: Union[LineItem, dict[str, Any]],
    ) -> LineItem:
        """Create or replace a line item (PUT).

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the parent order.
            line_item_id: The ID of the line item to create or replace.
            line_item: A ``LineItem`` model or dict of line item fields.

        Returns:
            The saved line item.
        """
        resp = await self._http.put(
            f"{self._base_path(direction, order_id)}/{line_item_id}",
            json=self._serialize(line_item),
        )
        return LineItem(**resp.json())

    async def patch(
        self, direction: OrderDirection, order_id: str, line_item_id: str, partial: dict[str, Any]
    ) -> LineItem:
        """Partially update a line item (PATCH).

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the parent order.
            line_item_id: The ID of the line item to update.
            partial: A dict of fields to update.

        Returns:
            The updated line item.
        """
        resp = await self._http.patch(
            f"{self._base_path(direction, order_id)}/{line_item_id}",
            json=partial,
        )
        return LineItem(**resp.json())

    async def delete(self, direction: OrderDirection, order_id: str, line_item_id: str) -> None:
        """Delete a line item.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the parent order.
            line_item_id: The ID of the line item to delete.
        """
        await self._http.delete(
            f"{self._base_path(direction, order_id)}/{line_item_id}",
        )
