from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class OrderCloudModel(BaseModel):
    """Base model for all OrderCloud resources."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Meta(BaseModel):
    """Pagination metadata returned with list responses."""

    Page: int = 0
    PageSize: int = 0
    TotalCount: int = 0
    TotalPages: int = 0
    ItemRange: list[int] = []
    NextPageKey: Optional[str] = None


class ListFacetValue(BaseModel):
    Value: str = ""
    Count: int = 0


class ListFacet(BaseModel):
    Name: str = ""
    XpPath: str = ""
    Values: list[ListFacetValue] = []


class MetaWithFacets(Meta):
    """Pagination metadata with search facets."""

    Facets: list[ListFacet] = []


class ListPage(BaseModel, Generic[T]):
    """A paginated list of items returned by the OrderCloud API."""

    Items: list[T] = []
    meta: "Meta" = Field(default_factory=Meta, alias="Meta")
