from typing import Any, Optional

from .shared import OrderCloudModel


class Category(OrderCloudModel):
    ID: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    ListOrder: Optional[int] = None
    Active: bool = True
    ParentID: Optional[str] = None
    ChildCount: int = 0
    xp: Optional[dict[str, Any]] = None
