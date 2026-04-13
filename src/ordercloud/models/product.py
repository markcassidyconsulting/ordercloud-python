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
        QuantityAvailable: Current quantity in stock.
        LastUpdated: ISO 8601 timestamp of last inventory update.
    """

    Enabled: bool = False
    NotificationPoint: Optional[int] = None
    VariantLevelTracking: bool = False
    OrderCanExceed: bool = False
    QuantityAvailable: int = 0
    LastUpdated: Optional[str] = None


class VariantInventory(OrderCloudModel):
    """Inventory data for a specific product variant.

    Attributes:
        QuantityAvailable: Current quantity in stock for this variant.
    """

    QuantityAvailable: int = 0


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
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    Active: bool = True
    ShipWeight: Optional[float] = None
    ShipHeight: Optional[float] = None
    ShipWidth: Optional[float] = None
    ShipLength: Optional[float] = None
    Inventory: Optional[VariantInventory] = None
    xp: Optional[dict[str, Any]] = None


class Product(OrderCloudModel):
    """An OrderCloud Product.

    Attributes:
        OwnerID: The ID of the organisation that owns this product.
        DefaultPriceScheduleID: ID of the default price schedule.
        AutoForward: Whether orders auto-forward to suppliers.
        ID: Unique identifier (auto-generated if not provided).
        ParentID: ID of the parent product (for variant parents).
        IsParent: Whether this product has variants.
        IsBundle: Whether this product is a bundle.
        Name: Display name of the product.
        Description: Optional description.
        QuantityMultiplier: Minimum order quantity increment.
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
    AutoForward: bool = False
    ID: Optional[str] = None
    ParentID: Optional[str] = None
    IsParent: bool = False
    IsBundle: bool = False
    Name: Optional[str] = None
    Description: Optional[str] = None
    QuantityMultiplier: int = 1
    ShipWeight: Optional[float] = None
    ShipHeight: Optional[float] = None
    ShipWidth: Optional[float] = None
    ShipLength: Optional[float] = None
    Active: bool = True
    SpecCount: int = 0
    VariantCount: int = 0
    ShipFromAddressID: Optional[str] = None
    Inventory: Optional[Inventory] = None
    DefaultSupplierID: Optional[str] = None
    AllSuppliersCanSell: bool = False
    Returnable: bool = False
    DateCreated: Optional[str] = None
    xp: Optional[dict[str, Any]] = None
