"""OrderCloud embedded types for line items (LineItemProduct, LineItemVariant)."""

from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["LineItemProduct", "LineItemVariant"]


class LineItemProduct(OrderCloudModel):
    """A product snapshot as embedded in a LineItem (read-only).

    This is a subset of the full Product model, representing the product
    state at the time the line item was created.

    Attributes:
        ID: Product ID.
        Name: Product display name.
        Description: Product description.
        Returnable: Whether the product can be returned.
        QuantityMultiplier: Order quantity increment.
        ShipWeight: Shipping weight.
        ShipHeight: Shipping height.
        ShipWidth: Shipping width.
        ShipLength: Shipping length.
        DefaultSupplierID: Default supplier for this product.
        ParentID: ID of the parent product.
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    Returnable: Optional[bool] = None
    QuantityMultiplier: Optional[int] = None
    ShipWeight: Optional[float] = None
    ShipHeight: Optional[float] = None
    ShipWidth: Optional[float] = None
    ShipLength: Optional[float] = None
    DefaultSupplierID: Optional[str] = None
    ParentID: Optional[str] = None
    xp: Optional[dict[str, Any]] = None


class LineItemVariant(OrderCloudModel):
    """A variant snapshot as embedded in a LineItem (read-only).

    Attributes:
        ID: Variant ID.
        Name: Variant display name.
        Description: Variant description.
        ShipWeight: Shipping weight override.
        ShipHeight: Shipping height override.
        ShipWidth: Shipping width override.
        ShipLength: Shipping length override.
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    ShipWeight: Optional[float] = None
    ShipHeight: Optional[float] = None
    ShipWidth: Optional[float] = None
    ShipLength: Optional[float] = None
    xp: Optional[dict[str, Any]] = None
