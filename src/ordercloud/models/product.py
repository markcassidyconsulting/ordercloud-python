"""OrderCloud Product, Variant, and Inventory models."""

from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["Inventory", "VariantInventory", "Variant", "Product"]


class Inventory(OrderCloudModel):
    """Inventory settings for a product.

    Attributes:
        Enabled: Whether inventory tracking is enabled.
        NotificationPoint: Stock level that triggers a notification.
        VariantLevelTracking: Whether inventory is tracked per variant.
        OrderCanExceed: Whether orders can exceed available stock.
        QuantityAvailable: Current quantity in stock.  Read-only when
            inventory records are used.
        LastUpdated: ISO 8601 timestamp of last inventory update (read-only).
    """

    Enabled: Optional[bool] = None
    NotificationPoint: Optional[int] = None
    VariantLevelTracking: Optional[bool] = None
    OrderCanExceed: Optional[bool] = None
    QuantityAvailable: int = 0
    LastUpdated: Optional[str] = None


class VariantInventory(OrderCloudModel):
    """Inventory data for a specific product variant.

    Attributes:
        QuantityAvailable: Current quantity in stock for this variant.
        NotificationPoint: Stock level that triggers a notification.
        LastUpdated: ISO 8601 timestamp of last update (read-only).
    """

    QuantityAvailable: int = 0
    NotificationPoint: Optional[int] = None
    LastUpdated: Optional[str] = None


class Variant(OrderCloudModel):
    """A product variant (e.g. size/colour combination).

    Attributes:
        ID: Unique identifier.
        Name: Display name of the variant.
        Description: Optional description.
        Active: Whether the variant is active.
        ShipWeight: Shipping weight override.
        ShipHeight: Shipping height override.
        ShipWidth: Shipping width override.
        ShipLength: Shipping length override.
        Inventory: Variant-level inventory data.
        Specs: Spec/option selections that define this variant (read-only).
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    Active: Optional[bool] = None
    ShipWeight: Optional[float] = None
    ShipHeight: Optional[float] = None
    ShipWidth: Optional[float] = None
    ShipLength: Optional[float] = None
    Inventory: Optional[VariantInventory] = None
    Specs: Optional[list[dict[str, Any]]] = None
    xp: Optional[dict[str, Any]] = None


class Product(OrderCloudModel):
    """An OrderCloud Product.

    Attributes:
        OwnerID: The ID of the organisation that owns this product.
        DefaultPriceScheduleID: ID of the default price schedule.
        AutoForward: Whether orders auto-forward to the default supplier.
        ID: Unique identifier (auto-generated if not provided).
        ParentID: ID of the parent product (for variant parents).
        IsParent: Whether this product has variants.
        IsBundle: Whether this product is a bundle (read-only).
        Name: Display name of the product.
        Description: Optional description.
        QuantityMultiplier: Minimum order quantity increment (default 1).
        ShipWeight: Shipping weight.
        ShipHeight: Shipping height.
        ShipWidth: Shipping width.
        ShipLength: Shipping length.
        Active: Whether the product is active.
        SpecCount: Number of specs defined (read-only).
        VariantCount: Number of variants generated (read-only).
        ShipFromAddressID: Default ship-from address.
        Inventory: Product-level inventory settings.
        DefaultSupplierID: Default supplier for this product.
        AllSuppliersCanSell: Whether all suppliers may sell this product.
        Returnable: Whether the product can be returned.
        DateCreated: ISO 8601 timestamp of creation (read-only).
        xp: Extended properties (arbitrary custom data).
    """

    OwnerID: Optional[str] = None
    DefaultPriceScheduleID: Optional[str] = None
    AutoForward: Optional[bool] = None
    ID: Optional[str] = None
    ParentID: Optional[str] = None
    IsParent: Optional[bool] = None
    IsBundle: Optional[bool] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    QuantityMultiplier: int = 1
    ShipWeight: Optional[float] = None
    ShipHeight: Optional[float] = None
    ShipWidth: Optional[float] = None
    ShipLength: Optional[float] = None
    Active: Optional[bool] = None
    SpecCount: int = 0
    VariantCount: int = 0
    ShipFromAddressID: Optional[str] = None
    Inventory: Optional[Inventory] = None
    DefaultSupplierID: Optional[str] = None
    AllSuppliersCanSell: Optional[bool] = None
    Returnable: Optional[bool] = None
    DateCreated: Optional[str] = None
    xp: Optional[dict[str, Any]] = None
