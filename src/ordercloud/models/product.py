from typing import Any, Optional

from .shared import OrderCloudModel


class Inventory(OrderCloudModel):
    Enabled: bool = False
    NotificationPoint: Optional[int] = None
    VariantLevelTracking: bool = False
    OrderCanExceed: bool = False
    QuantityAvailable: int = 0
    LastUpdated: Optional[str] = None


class VariantInventory(OrderCloudModel):
    QuantityAvailable: int = 0


class Variant(OrderCloudModel):
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
