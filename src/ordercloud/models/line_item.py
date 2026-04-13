"""OrderCloud LineItem model."""

from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["LineItem"]


class LineItem(OrderCloudModel):
    """A line item on an OrderCloud Order.

    Attributes:
        ID: Unique identifier (auto-generated if not provided).
        ProductID: ID of the product on this line.
        Quantity: Ordered quantity.
        DateAdded: ISO 8601 timestamp when the line was added (read-only).
        QuantityShipped: Quantity already shipped (read-only).
        UnitPrice: Price per unit (read-only, from price schedule).
        PromotionDiscount: Discount from promotions (read-only).
        LineTotal: Total for this line after discounts (read-only).
        LineSubtotal: Subtotal before discounts (read-only).
        CostCenter: Optional cost centre code.
        DateNeeded: Requested delivery date.
        ShippingAccount: Shipping account reference.
        ShippingAddressID: ID of the shipping address for this line.
        ShipFromAddressID: ID of the ship-from address.
        Product: Embedded product snapshot (read-only).
        Variant: Embedded variant snapshot (read-only).
        ShippingAddress: Embedded shipping address (read-only).
        ShipFromAddress: Embedded ship-from address (read-only).
        SupplierID: ID of the supplier fulfilling this line.
        InventoryRecordID: ID of the inventory record.
        PriceScheduleID: ID of the price schedule used.
        IsBundle: Whether this line is a bundle (read-only).
        xp: Extended properties (arbitrary custom data).
    """

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
