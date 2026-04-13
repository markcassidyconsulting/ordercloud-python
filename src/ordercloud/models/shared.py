"""Shared base classes and pagination types for OrderCloud models.

All OrderCloud API models use PascalCase field names to match the API's
JSON representation directly.  Python-side access is also PascalCase
(e.g. ``product.Name``, ``page.Meta.TotalCount``) — this is a deliberate
trade-off for zero-friction serialisation round-trips.
"""

from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")
XP = TypeVar("XP")

__all__ = [
    "OrderCloudModel",
    "OrderCloudEnum",
    "XP",
    "Meta",
    "ListFacetValue",
    "ListFacet",
    "MetaWithFacets",
    "ListPage",
]


class OrderCloudEnum(str, Enum):
    """Base for all OrderCloud string enums.

    Overrides ``__str__`` and ``__format__`` to return the raw value,
    ensuring consistent behaviour in f-strings across Python 3.10-3.13.
    (Python 3.11 changed ``Enum.__format__`` to include the class name.)
    """

    def __str__(self) -> str:
        return str(self.value)

    def __format__(self, format_spec: str) -> str:
        return str(self.value).__format__(format_spec)


class OrderCloudModel(BaseModel):
    """Base model for all OrderCloud API resources.

    Configured with ``populate_by_name=True`` so fields can be set by
    either their Python name or JSON alias, and ``extra="allow"`` so
    that unrecognised fields from the API (e.g. new additions) are
    preserved rather than dropped.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Meta(BaseModel):
    """Pagination metadata returned with list responses.

    Attributes:
        Page: Current 1-based page number.
        PageSize: Number of items per page.
        TotalCount: Total number of items matching the query.
        TotalPages: Total number of pages.
        ItemRange: Two-element list ``[first, last]`` item indices on this page.
        NextPageKey: Opaque key for cursor-based pagination (if available).
    """

    Page: int = 0
    PageSize: int = 0
    TotalCount: int = 0
    TotalPages: int = 0
    ItemRange: list[int] = Field(default_factory=list)
    NextPageKey: Optional[str] = None


class ListFacetValue(BaseModel):
    """A single value within a search facet.

    Attributes:
        Value: The facet value string.
        Count: Number of items matching this facet value.
    """

    Value: str = ""
    Count: int = 0


class ListFacet(BaseModel):
    """A search facet returned with product list responses.

    Attributes:
        Name: The facet field name.
        XpPath: The extended property path for this facet.
        Values: The individual facet values and their counts.
        xp: Extended properties (arbitrary custom data).
    """

    Name: str = ""
    XpPath: str = ""
    Values: list[ListFacetValue] = Field(default_factory=list)
    xp: Optional[dict[str, Any]] = None


class MetaWithFacets(Meta):
    """Pagination metadata with search facets (used by product search).

    Attributes:
        Facets: Search facets with value counts for refinement.
    """

    Facets: list[ListFacet] = Field(default_factory=list)


# Type alias so the ListPage.Meta field annotation doesn't collide with
# the field name itself — Pydantic resolves annotations in the class
# namespace where the field assignment would shadow the Meta class.
_Meta = Meta


class ListPage(BaseModel, Generic[T]):
    """A paginated list of items returned by the OrderCloud API.

    Attributes:
        Items: The items on this page.
        Meta: Pagination metadata.
    """

    Items: list[T] = Field(default_factory=list)
    Meta: _Meta = Field(default_factory=Meta)
