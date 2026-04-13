from typing import Any, Optional

from .shared import OrderCloudModel


class Buyer(OrderCloudModel):
    ID: Optional[str] = None
    Name: Optional[str] = None
    GroupID: Optional[str] = None
    DefaultCatalogID: Optional[str] = None
    Active: bool = True
    DateCreated: Optional[str] = None
    xp: Optional[dict[str, Any]] = None
