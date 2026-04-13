"""OpenAPI type to Python type annotation mapping.

Maps OpenAPI schema types/formats to the Python type patterns used in
the hand-written Phase 1 SDK code.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "extract_ref",
    "map_type",
    "map_field",
]


def extract_ref(schema: dict[str, Any]) -> str | None:
    """Extract a schema name from a ``$ref``, handling ``allOf`` wrappers.

    The OrderCloud spec uses single-element ``allOf`` as a wrapper around
    ``$ref`` (to attach ``required`` or ``readOnly``).  This function
    handles both the direct and wrapped cases.
    """
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "allOf" in schema:
        items = schema["allOf"]
        if len(items) == 1 and "$ref" in items[0]:
            return items[0]["$ref"].rsplit("/", 1)[-1]
    return None


def map_type(
    schema: dict[str, Any],
    *,
    read_only: bool = False,
) -> tuple[str, str]:
    """Map an OpenAPI schema to a Python type annotation and default value.

    Returns a ``(python_type, default)`` tuple where both values are
    ready to emit as source code.
    """
    spec_default = schema.get("default")
    type_str = schema.get("type", "")

    # $ref or allOf wrapper → Optional model/enum reference.
    ref_name = extract_ref(schema)
    if ref_name:
        return f"Optional[{ref_name}]", "None"

    # Array types.
    if type_str == "array":
        items = schema.get("items", {})
        item_type = _resolve_item_type(items)
        return f"Optional[list[{item_type}]]", "None"

    # Object (xp and filters).
    if type_str == "object":
        return "Optional[dict[str, Any]]", "None"

    # Primitive types with spec-level defaults.
    if spec_default is not None:
        py_type = _bare_primitive(type_str)
        return py_type, repr(spec_default)

    # Read-only primitives with numeric defaults.
    if read_only:
        if type_str == "integer":
            return "int", "0"
        if type_str == "number":
            return "float", "0.0"

    # Standard primitives (Optional).
    return _optional_primitive(type_str)


# ---------------------------------------------------------------------------
# Primitive mapping helpers
# ---------------------------------------------------------------------------

_PRIMITIVE_MAP: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}


def _bare_primitive(type_str: str) -> str:
    """Map an OpenAPI primitive to a bare Python type (no Optional)."""
    return _PRIMITIVE_MAP.get(type_str, "Any")


def _optional_primitive(type_str: str) -> tuple[str, str]:
    """Map an OpenAPI primitive to ``Optional[T]`` with ``None`` default."""
    bare = _PRIMITIVE_MAP.get(type_str, "Any")
    return f"Optional[{bare}]", "None"


def _resolve_item_type(items_schema: dict[str, Any]) -> str:
    """Resolve the Python type for array items."""
    ref_name = extract_ref(items_schema)
    if ref_name:
        return ref_name
    type_str = items_schema.get("type", "")
    if type_str == "object":
        return "dict[str, Any]"
    return _bare_primitive(type_str)


# ---------------------------------------------------------------------------
# Full field mapping (returns metadata alongside type info)
# ---------------------------------------------------------------------------


def map_field(
    prop_name: str,
    prop_schema: dict[str, Any],
    *,
    enum_names: set[str] | None = None,
) -> tuple[str, str, bool, bool, bool, str | None]:
    """Map an OpenAPI property to full field metadata.

    Returns:
        Tuple of ``(python_type, default, is_xp, is_enum_ref, is_model_ref, ref_type)``.
    """
    enum_names = enum_names or set()
    read_only = prop_schema.get("readOnly", False)
    is_xp = prop_name == "xp"

    # Direct $ref.
    ref_name = extract_ref(prop_schema)
    if ref_name:
        is_enum = ref_name in enum_names
        if is_enum:
            return f"Optional[{ref_name}]", "None", is_xp, True, False, ref_name
        return f"Optional[{ref_name}]", "None", is_xp, False, True, ref_name

    # Array with $ref items.
    if prop_schema.get("type") == "array":
        items = prop_schema.get("items", {})
        item_ref = extract_ref(items)
        if item_ref:
            is_enum = item_ref in enum_names
            return (
                f"Optional[list[{item_ref}]]",
                "None",
                is_xp,
                is_enum,
                not is_enum,
                item_ref,
            )

    # Delegate to map_type for everything else.
    python_type, default = map_type(prop_schema, read_only=read_only)
    return python_type, default, is_xp, False, False, None
