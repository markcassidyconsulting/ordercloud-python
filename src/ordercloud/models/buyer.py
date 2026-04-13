"""OrderCloud Buyer model."""

from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["Buyer"]


class Buyer(OrderCloudModel):
    """An OrderCloud Buyer organisation.

    Attributes:
        ID: Unique identifier (auto-generated if not provided).
        Name: Display name of the buyer.
        GroupID: Optional group identifier.
        DefaultCatalogID: The catalog assigned to this buyer by default.
        Active: Whether the buyer is active.
        DateCreated: ISO 8601 timestamp of creation (read-only).
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    Name: Optional[str] = None
    GroupID: Optional[str] = None
    DefaultCatalogID: Optional[str] = None
    Active: bool = True
    DateCreated: Optional[str] = None
    xp: Optional[dict[str, Any]] = None
