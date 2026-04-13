from enum import Enum
from typing import Any, Optional

from .shared import OrderCloudModel


class OrderStatus(str, Enum):
    Unsubmitted = "Unsubmitted"
    AwaitingApproval = "AwaitingApproval"
    Declined = "Declined"
    Open = "Open"
    Completed = "Completed"
    Canceled = "Canceled"


class Order(OrderCloudModel):
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
