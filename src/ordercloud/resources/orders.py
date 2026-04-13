"""OrderCloud Orders API resource."""

from typing import Any, Optional, Union

from ..models.order import Order, OrderDirection
from ..models.shared import ListPage
from .base import BaseResource

__all__ = ["OrdersResource"]


class OrdersResource(BaseResource):
    """Operations on OrderCloud Orders."""

    async def list(
        self,
        direction: OrderDirection = OrderDirection.Incoming,
        *,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> ListPage[Order]:
        """List orders with optional filtering and pagination.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            search: Free-text search term.
            sort_by: Field name to sort by (prefix with ``!`` to reverse).
            page: 1-based page number.
            page_size: Number of items per page (max 100).
            filters: Arbitrary key/value filters.

        Returns:
            A paginated list of orders.
        """
        params = self._build_list_params(
            search=search,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            filters=filters,
        )
        resp = await self._http.get(f"/orders/{direction}", **params)
        return self._parse_list(resp.json(), Order)

    async def get(self, direction: OrderDirection, order_id: str) -> Order:
        """Retrieve a single order by ID.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the order.

        Returns:
            The requested order.
        """
        resp = await self._http.get(f"/orders/{direction}/{order_id}")
        return Order(**resp.json())

    async def create(self, direction: OrderDirection, order: Union[Order, dict[str, Any]]) -> Order:
        """Create a new order.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order: An ``Order`` model or dict of order fields.

        Returns:
            The created order (with server-assigned fields populated).
        """
        resp = await self._http.post(f"/orders/{direction}", json=self._serialize(order))
        return Order(**resp.json())

    async def save(
        self, direction: OrderDirection, order_id: str, order: Union[Order, dict[str, Any]]
    ) -> Order:
        """Create or replace an order (PUT).

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the order to create or replace.
            order: An ``Order`` model or dict of order fields.

        Returns:
            The saved order.
        """
        resp = await self._http.put(
            f"/orders/{direction}/{order_id}",
            json=self._serialize(order),
        )
        return Order(**resp.json())

    async def patch(
        self, direction: OrderDirection, order_id: str, partial: dict[str, Any]
    ) -> Order:
        """Partially update an order (PATCH).

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the order to update.
            partial: A dict of fields to update.

        Returns:
            The updated order.
        """
        resp = await self._http.patch(f"/orders/{direction}/{order_id}", json=partial)
        return Order(**resp.json())

    async def delete(self, direction: OrderDirection, order_id: str) -> None:
        """Delete an order.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the order to delete.
        """
        await self._http.delete(f"/orders/{direction}/{order_id}")

    async def submit(self, direction: OrderDirection, order_id: str) -> Order:
        """Submit an order for approval or fulfillment.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the order to submit.

        Returns:
            The submitted order.
        """
        resp = await self._http.post(f"/orders/{direction}/{order_id}/submit")
        return Order(**resp.json())

    async def approve(self, direction: OrderDirection, order_id: str, comments: str = "") -> Order:
        """Approve a submitted order.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the order to approve.
            comments: Optional approval comments.

        Returns:
            The approved order.
        """
        resp = await self._http.post(
            f"/orders/{direction}/{order_id}/approve",
            json={"Comments": comments},
        )
        return Order(**resp.json())

    async def cancel(self, direction: OrderDirection, order_id: str) -> Order:
        """Cancel an order.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the order to cancel.

        Returns:
            The cancelled order.
        """
        resp = await self._http.post(f"/orders/{direction}/{order_id}/cancel")
        return Order(**resp.json())

    async def complete(self, direction: OrderDirection, order_id: str) -> Order:
        """Mark an order as complete.

        Args:
            direction: Order direction — ``"Incoming"`` or ``"Outgoing"``.
            order_id: The ID of the order to complete.

        Returns:
            The completed order.
        """
        resp = await self._http.post(f"/orders/{direction}/{order_id}/complete")
        return Order(**resp.json())
