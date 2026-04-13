"""OrderCloud user models (OrderUser, Locale)."""

from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["Locale", "OrderUser"]


class Locale(OrderCloudModel):
    """A locale assignment for a user.

    Attributes:
        ID: Unique identifier.
        OwnerID: ID of the organisation that owns this locale.
        Currency: Currency code (recommended: ISO 4217).
        Language: Language code (recommended: ISO 639 + ISO 3166, e.g. ``en-US``).
    """

    ID: Optional[str] = None
    OwnerID: Optional[str] = None
    Currency: Optional[str] = None
    Language: Optional[str] = None


# Type alias — avoids Pydantic field/type name collision in OrderUser.Locale
_Locale = Locale


class OrderUser(OrderCloudModel):
    """A user as embedded in an Order (read-only snapshot).

    Attributes:
        ID: Unique identifier.
        CompanyID: ID of the user's company (read-only).
        Username: Unique username across all organisations.
        FirstName: User's first name.
        LastName: User's last name.
        Email: User's email address.
        Phone: User's phone number.
        TermsAccepted: ISO 8601 timestamp when terms were accepted.
        Active: Whether the user is active.
        xp: Extended properties (arbitrary custom data).
        AvailableRoles: Roles available via security profile assignments (read-only).
        Locale: Most specific locale assigned to the user (read-only).
        DateCreated: ISO 8601 timestamp of creation (read-only).
        LastActive: ISO 8601 timestamp of last activity (read-only).
        PasswordLastSetDate: ISO 8601 timestamp of last password change (read-only).
    """

    ID: Optional[str] = None
    CompanyID: Optional[str] = None
    Username: Optional[str] = None
    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    TermsAccepted: Optional[str] = None
    Active: Optional[bool] = None
    xp: Optional[dict[str, Any]] = None
    AvailableRoles: Optional[list[str]] = None
    Locale: Optional[_Locale] = None
    DateCreated: Optional[str] = None
    LastActive: Optional[str] = None
    PasswordLastSetDate: Optional[str] = None
