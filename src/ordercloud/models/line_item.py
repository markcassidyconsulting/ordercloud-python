from typing import Any, Optional

from .shared import OrderCloudModel


class LineItem(OrderCloudModel):
    ID: Optional[str] = None
    ProductID: Optional[str] = None
    Quantity: int = 0
    DateAdded: Optional[str] = None
    QuantityShipped: int = 0
    UnitPrice: Optional[float] = None
    PromotionDiscount: float = 0.0
    LineTotal: float = 0.0
    LineSubtotal: float = 0.0
    CostCenter: Optional[str] = None
    DateNeeded: Optional[str] = None
    ShippingAccount: Optional[str] = None
    ShippingAddressID: Optional[str] = None
    ShipFromAddressID: Optional[str] = None
    Product: Optional[dict[str, Any]] = None
    Variant: Optional[dict[str, Any]] = None
    ShippingAddress: Optional[dict[str, Any]] = None
    ShipFromAddress: Optional[dict[str, Any]] = None
    SupplierID: Optional[str] = None
    InventoryRecordID: Optional[str] = None
    PriceScheduleID: Optional[str] = None
    IsBundle: bool = False
    xp: Optional[dict[str, Any]] = None
