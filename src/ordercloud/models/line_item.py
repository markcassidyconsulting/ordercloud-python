"""OrderCloud LineItem model."""

from typing import Any, Optional

from .address import Address
from .line_item_types import LineItemProduct, LineItemVariant
from .shared import OrderCloudModel

__all__ = ["LineItem"]


class LineItem(OrderCloudModel):
    """A line item on an OrderCloud Order.

    Attributes:
        ID: Unique identifier (auto-generated if not provided).
        ProductID: ID of the product on this line.
        Quantity: Ordered quantity (default 1, minimum 1).
        BundleItemID: ID of the bundle line item this belongs to (read-only).
        IsBundle: Whether this line represents a bundle (read-only).
        DateAdded: ISO 8601 timestamp when the line was added (read-only).
        QuantityShipped: Quantity already shipped (read-only).
        UnitPrice: Price per unit (writable with OverrideUnitPrice role).
        PromotionDiscount: Discount from promotions (read-only).
        BaseDiscount: Discount from discount assignments (read-only).
        DiscountID: ID of the applied discount (read-only).
        LineTotal: Total after discounts (read-only).
        LineSubtotal: Subtotal before discounts (read-only).
        CostCenter: Optional cost centre code (reference only).
        DateNeeded: Requested delivery date.
        ShippingAccount: Shipping account reference (reference only).
        ShippingAddressID: ID of the shipping address for this line.
        ShipFromAddressID: ID of the ship-from address.
        Product: Embedded product snapshot (read-only).
        Variant: Embedded variant snapshot (read-only).
        ShippingAddress: Embedded shipping address (read-only).
        ShipFromAddress: Embedded ship-from address (read-only).
        SupplierID: ID of the supplier fulfilling this line (read-only).
        InventoryRecordID: ID of the inventory record.
        PriceScheduleID: ID of the price schedule used (read-only).
        IsOnSale: Whether a sale price is active (read-only).
        PriceOverridden: Whether UnitPrice was overridden (read-only).
        Specs: Spec/option selections on this line item.
        IncomingOrderID: ID of the original order (read-only, marketplace owner).
        OutgoingOrderID: ID of the forwarded order (read-only, marketplace owner).
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    ProductID: Optional[str] = None
    Quantity: int = 1
    BundleItemID: Optional[str] = None
    IsBundle: Optional[bool] = None
    DateAdded: Optional[str] = None
    QuantityShipped: int = 0
    UnitPrice: Optional[float] = None
    PromotionDiscount: float = 0.0
    BaseDiscount: float = 0.0
    DiscountID: Optional[str] = None
    LineTotal: float = 0.0
    LineSubtotal: float = 0.0
    CostCenter: Optional[str] = None
    DateNeeded: Optional[str] = None
    ShippingAccount: Optional[str] = None
    ShippingAddressID: Optional[str] = None
    ShipFromAddressID: Optional[str] = None
    Product: Optional[LineItemProduct] = None
    Variant: Optional[LineItemVariant] = None
    ShippingAddress: Optional[Address] = None
    ShipFromAddress: Optional[Address] = None
    SupplierID: Optional[str] = None
    InventoryRecordID: Optional[str] = None
    PriceScheduleID: Optional[str] = None
    IsOnSale: Optional[bool] = None
    PriceOverridden: Optional[bool] = None
    Specs: Optional[list[dict[str, Any]]] = None
    IncomingOrderID: Optional[str] = None
    OutgoingOrderID: Optional[str] = None
    xp: Optional[dict[str, Any]] = None
