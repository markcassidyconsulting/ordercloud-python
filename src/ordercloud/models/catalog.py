"""OrderCloud Catalog model."""

from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["Catalog"]


class Catalog(OrderCloudModel):
    """An OrderCloud Catalog.

    Attributes:
        ID: Unique identifier (auto-generated if not provided).
        OwnerID: The ID of the organisation that owns this catalog.
        Name: Display name of the catalog.
        Description: Optional description.
        Active: Whether the catalog is active.
        CategoryCount: Number of categories in this catalog (read-only).
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    OwnerID: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    Active: bool = True
    CategoryCount: int = 0
    xp: Optional[dict[str, Any]] = None
