"""OrderCloud Address model."""

from typing import Any, Optional

from .shared import OrderCloudModel

__all__ = ["Address"]


class Address(OrderCloudModel):
    """An OrderCloud Address.

    Used for billing addresses, shipping addresses, and ship-from
    addresses across orders and line items.

    Attributes:
        ID: Unique identifier.
        DateCreated: ISO 8601 timestamp of creation (read-only).
        CompanyName: Company name at this address.
        FirstName: Contact first name.
        LastName: Contact last name.
        Street1: Street address line 1.
        Street2: Street address line 2.
        City: City name.
        State: State or province (required for US/CA).
        Zip: Postal code (required for US/CA).
        Country: Two-letter country code (ISO 3166).
        Phone: Phone number.
        AddressName: Friendly name for this address.
        xp: Extended properties (arbitrary custom data).
    """

    ID: Optional[str] = None
    DateCreated: Optional[str] = None
    CompanyName: Optional[str] = None
    FirstName: Optional[str] = None
    LastName: Optional[str] = None
    Street1: Optional[str] = None
    Street2: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Zip: Optional[str] = None
    Country: Optional[str] = None
    Phone: Optional[str] = None
    AddressName: Optional[str] = None
    xp: Optional[dict[str, Any]] = None
