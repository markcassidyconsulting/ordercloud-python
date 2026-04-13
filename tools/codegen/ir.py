"""Intermediate representation for the codegen pipeline.

These dataclasses form the contract between parser, transformer, and
renderer.  Each captures exactly what a Jinja2 template needs — no
OpenAPI concepts leak through.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "FieldDef",
    "EnumDef",
    "ModelDef",
    "ModelGroup",
    "ParamDef",
    "OperationDef",
    "ResourceDef",
]


@dataclass
class FieldDef:
    """A single field on a Pydantic model."""

    name: str
    """PascalCase field name matching the API JSON key (used as Pydantic alias)."""

    python_name: str
    """snake_case Python field name."""

    python_type: str
    """Fully-qualified Python type annotation, e.g. ``Optional[str]``."""

    default: str
    """Default value as a Python source literal, e.g. ``Field(None, alias="Name")``."""

    description: str
    """Human-readable description for docstrings."""

    read_only: bool = False
    """Whether the API treats this field as read-only."""

    is_xp: bool = False
    """Whether this is the ``xp`` extended-properties field."""

    is_enum_ref: bool = False
    """Whether this field references an enum type."""

    is_model_ref: bool = False
    """Whether this field references another model type."""

    is_list: bool = False
    """Whether this is a list/array field."""

    ref_type: str | None = None
    """Name of the referenced model or enum, if applicable."""


@dataclass
class EnumDef:
    """A string enum type (``str, Enum`` dual-inheritance)."""

    name: str
    """PascalCase enum class name."""

    values: list[str]
    """Enum member values (PascalCase, matching their string representation)."""

    description: str
    """Docstring for the enum class."""


@dataclass
class ModelDef:
    """A Pydantic model class (extends ``OrderCloudModel``)."""

    name: str
    """PascalCase class name."""

    fields: list[FieldDef]
    """Fields in declaration order."""

    description: str
    """Docstring for the model class."""

    has_xp: bool = False
    """Whether this model has an ``xp`` field."""


@dataclass
class ModelGroup:
    """A group of related models that map to a single ``.py`` file."""

    module_name: str
    """Snake_case module name (without ``.py``), e.g. ``product``."""

    module_docstring: str
    """First-line docstring for the module."""

    models: list[ModelDef] = field(default_factory=list)
    """Models in dependency order (dependencies first)."""

    enums: list[EnumDef] = field(default_factory=list)
    """Enums used by models in this group."""

    imports: list[str] = field(default_factory=list)
    """Cross-module import lines needed by this file."""

    all_names: list[str] = field(default_factory=list)
    """Names to include in ``__all__``."""

    type_aliases: list[tuple[str, str]] = field(default_factory=list)
    """Aliases for imported types (emit after imports, before classes)."""

    type_aliases_bottom: list[tuple[str, str]] = field(default_factory=list)
    """Aliases for locally-defined types (emit after all classes)."""


@dataclass
class ParamDef:
    """A parameter on an API operation."""

    name: str
    """Parameter name (snake_case for query/path params, PascalCase for body)."""

    python_type: str
    """Python type annotation."""

    description: str
    """Human-readable description for docstrings."""

    location: str
    """One of ``path``, ``query``, ``body``."""

    required: bool = True
    """Whether this parameter is required."""

    default: str | None = None
    """Default value as a Python source literal, or ``None`` if no default."""

    is_enum: bool = False
    """Whether this is an enum-typed parameter."""

    enum_type: str | None = None
    """Name of the enum type, if applicable."""

    api_name: str | None = None
    """Original API parameter name (for query params where Python name differs)."""


@dataclass
class OperationDef:
    """A single API operation (one HTTP method on one path)."""

    method_name: str
    """Snake_case Python method name, e.g. ``list``, ``submit``."""

    http_method: str
    """Lowercase HTTP verb: ``get``, ``post``, ``put``, ``patch``, ``delete``."""

    path_template: str
    """f-string-ready URL path, e.g. ``/products/{product_id}``."""

    summary: str
    """Short summary for the method docstring."""

    description: str
    """Longer description (may be empty)."""

    path_params: list[ParamDef] = field(default_factory=list)
    """Positional parameters extracted from the URL path."""

    query_params: list[ParamDef] = field(default_factory=list)
    """Keyword-only parameters for query string."""

    body_param: ParamDef | None = None
    """Request body parameter, if any."""

    body_model: str | None = None
    """Name of the Pydantic model for the body, if applicable."""

    return_type: str | None = None
    """Name of the return model, or ``None`` for void operations."""

    return_is_list: bool = False
    """Whether the response is a paginated list."""

    uses_facet_meta: bool = False
    """Whether the list response uses ``MetaWithFacets`` instead of ``Meta``."""

    operation_id: str = ""
    """Original operationId from the spec, for reference."""

    required_fields: list[str] = field(default_factory=list)
    """Field names required by this operation's request body (for docstrings)."""


@dataclass
class ResourceDef:
    """A resource client class (extends ``BaseResource``)."""

    class_name: str
    """PascalCase class name, e.g. ``ProductsResource``."""

    module_name: str
    """Snake_case module filename (without ``.py``), e.g. ``products``."""

    attribute_name: str
    """Snake_case attribute name on ``OrderCloudClient``, e.g. ``products``."""

    module_docstring: str
    """First-line docstring for the module."""

    class_docstring: str
    """Docstring for the resource class."""

    operations: list[OperationDef] = field(default_factory=list)
    """All operations on this resource, in spec order."""

    model_imports: list[str] = field(default_factory=list)
    """Model names that need importing (e.g. ``["Product", "Inventory"]``)."""

    enum_imports: list[str] = field(default_factory=list)
    """Enum names that need importing."""

    import_lines: list[str] = field(default_factory=list)
    """Fully-formed import lines for the module header."""
