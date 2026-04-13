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
            Auto-created if not specified on create.
        Active: Whether the buyer is active.  If false, all user
            authentication is blocked.
        DateCreated: ISO 8601 timestamp of creation (read-only).
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    Name: Optional[str] = None
    GroupID: Optional[str] = None
    DefaultCatalogID: Optional[str] = None
    Active: Optional[bool] = None
    DateCreated: Optional[str] = None
    xp: Optional[dict[str, Any]] = None
