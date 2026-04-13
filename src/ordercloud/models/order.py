"""OrderCloud Order model and status enum."""

from enum import Enum
from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["OrderDirection", "OrderStatus", "Order"]


class OrderDirection(str, Enum):
    """Direction of an order relative to the authenticated user."""

    Incoming = "Incoming"
    Outgoing = "Outgoing"


class OrderStatus(str, Enum):
    """Possible states of an OrderCloud order."""

    Unsubmitted = "Unsubmitted"
    AwaitingApproval = "AwaitingApproval"
    Declined = "Declined"
    Open = "Open"
    Completed = "Completed"
    Canceled = "Canceled"


class Order(OrderCloudModel):
    """An OrderCloud Order.

    Attributes:
        ID: Unique identifier (auto-generated if not provided).
        FromUser: Embedded user object for the order creator (read-only).
        FromCompanyID: ID of the company placing the order.
        ToCompanyID: ID of the company receiving the order.
        FromUserID: ID of the user who placed the order.
        BillingAddressID: ID of the billing address.
        BillingAddress: Embedded billing address object (read-only).
        ShippingAddressID: ID of the shipping address.
        Comments: Free-text comments on the order.
        LineItemCount: Number of line items (read-only).
        Status: Current order status.
        DateCreated: ISO 8601 timestamp of creation (read-only).
        DateSubmitted: ISO 8601 timestamp of submission (read-only).
        DateApproved: ISO 8601 timestamp of approval (read-only).
        DateDeclined: ISO 8601 timestamp of decline (read-only).
        DateCanceled: ISO 8601 timestamp of cancellation (read-only).
        DateCompleted: ISO 8601 timestamp of completion (read-only).
        Subtotal: Order subtotal before shipping and tax (read-only).
        ShippingCost: Shipping cost (read-only).
        TaxCost: Tax amount (read-only).
        PromotionDiscount: Total promotion discount (read-only).
        Total: Order grand total (read-only).
        IsSubmitted: Whether the order has been submitted (read-only).
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    FromUser: Optional[dict[str, Any]] = None
    FromCompanyID: Optional[str] = None
    ToCompanyID: Optional[str] = None
    FromUserID: Optional[str] = None
    BillingAddressID: Optional[str] = None
    BillingAddress: Optional[dict[str, Any]] = None
    ShippingAddressID: Optional[str] = None
    Comments: Optional[str] = None
    LineItemCount: int = 0
    Status: Optional[OrderStatus] = None
    DateCreated: Optional[str] = None
    DateSubmitted: Optional[str] = None
    DateApproved: Optional[str] = None
    DateDeclined: Optional[str] = None
    DateCanceled: Optional[str] = None
    DateCompleted: Optional[str] = None
    Subtotal: float = 0.0
    ShippingCost: float = 0.0
    TaxCost: float = 0.0
    PromotionDiscount: float = 0.0
    Total: float = 0.0
    IsSubmitted: bool = False
    xp: Optional[dict[str, Any]] = None
