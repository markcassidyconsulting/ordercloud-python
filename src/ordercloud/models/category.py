"""OrderCloud Category model."""

from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["Category"]


class Category(OrderCloudModel):
    """An OrderCloud Category (belongs to a Catalog).

    Attributes:
        ID: Unique identifier (auto-generated if not provided).
        Name: Display name of the category.
        Description: Optional description.
        ListOrder: Sort order among sibling categories (minimum 0).
        Active: Whether the category is active.  If false, buyers cannot
            see this category or any categories or products under it.
        ParentID: ID of the parent category (``None`` for top-level).
        ChildCount: Number of direct child categories (read-only).
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    ListOrder: Optional[int] = None
    Active: Optional[bool] = None
    ParentID: Optional[str] = None
    ChildCount: int = 0
    xp: Optional[dict[str, Any]] = None
