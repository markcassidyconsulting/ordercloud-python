"""OrderCloud Order model, status enum, and direction enum."""

from enum import Enum
from typing import Any, Optional

from .address import Address
from .shared import OrderCloudModel
from .user import OrderUser

__all__ = ["OrderDirection", "OrderStatus", "Order"]


class OrderDirection(str, Enum):
    """Direction of an order relative to the authenticated user."""

    Incoming = "Incoming"
    Outgoing = "Outgoing"
    All = "All"


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
        Status: Current order status (read-only).
        DateCreated: ISO 8601 timestamp of creation (read-only).
        DateSubmitted: ISO 8601 timestamp of submission (read-only).
        DateApproved: ISO 8601 timestamp of approval (read-only).
        DateDeclined: ISO 8601 timestamp of decline (read-only).
        DateCanceled: ISO 8601 timestamp of cancellation (read-only).
        DateCompleted: ISO 8601 timestamp of completion (read-only).
        LastUpdated: ISO 8601 timestamp of last update (read-only).
        Subtotal: Order subtotal before shipping and tax (read-only).
        ShippingCost: Shipping cost (writable with OverrideShipping role).
        TaxCost: Tax amount (writable with TaxOverride role).
        Gratuity: Gratuity amount (default 0).
        Fees: Fees associated with the order (read-only).
        BaseDiscount: Sum of discount assignment amounts (read-only).
        PromotionDiscount: Sum of promotion amounts (read-only).
        Currency: Currency code inherited from the buyer (read-only).
        Total: Grand total (read-only).
        IsSubmitted: Whether the order has been submitted (read-only).
        SubscriptionID: ID of the subscription for automated orders (read-only).
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    FromUser: Optional[OrderUser] = None
    FromCompanyID: Optional[str] = None
    ToCompanyID: Optional[str] = None
    FromUserID: Optional[str] = None
    BillingAddressID: Optional[str] = None
    BillingAddress: Optional[Address] = None
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
    LastUpdated: Optional[str] = None
    Subtotal: float = 0.0
    ShippingCost: float = 0.0
    TaxCost: float = 0.0
    Gratuity: float = 0.0
    Fees: float = 0.0
    BaseDiscount: float = 0.0
    PromotionDiscount: float = 0.0
    Currency: Optional[str] = None
    Total: float = 0.0
    IsSubmitted: Optional[bool] = None
    SubscriptionID: Optional[str] = None
    xp: Optional[dict[str, Any]] = None
