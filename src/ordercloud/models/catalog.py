from typing import Any, Optional

from .shared import OrderCloudModel


class Catalog(OrderCloudModel):
    ID: Optional[str] = None
    OwnerID: Optional[str] = None
    Name: Optional[str] = None
    Description: Optional[str] = None
    Active: bool = True
    CategoryCount: int = 0
    xp: Optional[dict[str, Any]] = None
