"""Shared base classes and pagination types for OrderCloud models.

Generated models use snake_case field names with ``Field(alias="PascalCase")``
so that Python-side access is idiomatic (e.g. ``product.name``,
``page.meta.total_count``) while JSON serialisation still uses PascalCase
to match the OrderCloud API.
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
        page: Current 1-based page number.
        page_size: Number of items per page.
        total_count: Total number of items matching the query.
        total_pages: Total number of pages.
        item_range: Two-element list ``[first, last]`` item indices on this page.
        next_page_key: Opaque key for cursor-based pagination (if available).
    """

    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(0, alias="Page")
    page_size: int = Field(0, alias="PageSize")
    total_count: int = Field(0, alias="TotalCount")
    total_pages: int = Field(0, alias="TotalPages")
    item_range: list[int] = Field(default_factory=list, alias="ItemRange")
    next_page_key: Optional[str] = Field(None, alias="NextPageKey")


class ListFacetValue(BaseModel):
    """A single value within a search facet.

    Attributes:
        value: The facet value string.
        count: Number of items matching this facet value.
    """

    model_config = ConfigDict(populate_by_name=True)

    value: str = Field("", alias="Value")
    count: int = Field(0, alias="Count")


class ListFacet(BaseModel):
    """A search facet returned with product list responses.

    Attributes:
        name: The facet field name.
        xp_path: The extended property path for this facet.
        values: The individual facet values and their counts.
        xp: Extended properties (arbitrary custom data).
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field("", alias="Name")
    xp_path: str = Field("", alias="XpPath")
    values: list[ListFacetValue] = Field(default_factory=list, alias="Values")
    xp: Optional[dict[str, Any]] = Field(None, alias="xp")


class MetaWithFacets(Meta):
    """Pagination metadata with search facets (used by product search).

    Attributes:
        facets: Search facets with value counts for refinement.
    """

    facets: list[ListFacet] = Field(default_factory=list, alias="Facets")


class ListPage(BaseModel, Generic[T]):
    """A paginated list of items returned by the OrderCloud API.

    Attributes:
        items: The items on this page.
        meta: Pagination metadata.
    """

    model_config = ConfigDict(populate_by_name=True)

    items: list[T] = Field(default_factory=list, alias="Items")
    meta: Meta = Field(default_factory=Meta, alias="Meta")
