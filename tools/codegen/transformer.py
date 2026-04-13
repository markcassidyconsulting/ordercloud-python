"""Transformer — enriches raw IR with Python-specific concerns.

Takes the raw ModelDef/EnumDef/ResourceDef objects from the parser and
produces ModelGroup objects (ready for template rendering) plus enriched
ResourceDef objects with computed import lines.
"""

from __future__ import annotations

from collections import defaultdict

from .grouping import MANUAL_SCHEMAS, RE_EXPORTS, SCHEMA_GROUPS
from .ir import (
    EnumDef,
    ModelDef,
    ModelGroup,
    ResourceDef,
)

__all__ = ["transform"]


# Types that live in shared.py (manual) and are importable from there.
# Superset of MANUAL_SCHEMAS — includes base classes that aren't spec schemas.
_SHARED_TYPES = MANUAL_SCHEMAS | {"OrderCloudModel", "ListPage"}


def transform(
    models: dict[str, ModelDef],
    enums: dict[str, EnumDef],
    resources: dict[str, ResourceDef],
) -> tuple[list[ModelGroup], list[ResourceDef]]:
    """Transform raw IR into render-ready structures.

    Returns:
        A tuple of ``(model_groups, resources)`` ready for template rendering.
    """
    # Build lookup: schema name → module name.
    schema_to_module = _build_schema_module_map()

    # Build model groups.
    model_groups = _build_model_groups(models, enums, schema_to_module)

    # Enrich resources.
    enriched_resources = _enrich_resources(resources, enums, schema_to_module)

    return model_groups, enriched_resources


# ---------------------------------------------------------------------------
# Model grouping
# ---------------------------------------------------------------------------


def _build_schema_module_map() -> dict[str, str]:
    """Build a map from schema name to its module name."""
    mapping: dict[str, str] = {}
    for module_name, schema_names in SCHEMA_GROUPS.items():
        for name in schema_names:
            mapping[name] = module_name
    return mapping


def _build_model_groups(
    models: dict[str, ModelDef],
    enums: dict[str, EnumDef],
    schema_to_module: dict[str, str],
) -> list[ModelGroup]:
    """Assemble ModelGroup objects from the grouping map."""
    groups: list[ModelGroup] = []

    for module_name, schema_names in SCHEMA_GROUPS.items():
        group_models: list[ModelDef] = []
        group_enums: list[EnumDef] = []
        cross_imports: set[tuple[str, str]] = set()  # (module, name)
        needs_any = False
        needs_optional = False
        needs_enum = False
        needs_field = False

        needs_generic = False
        needs_xp_typevar = False

        for name in schema_names:
            if name in enums:
                group_enums.append(enums[name])
            elif name in models:
                model = models[name]
                group_models.append(model)

                # Rewrite xp fields to use the XP TypeVar.
                if model.has_xp:
                    needs_generic = True
                    needs_xp_typevar = True
                    for field in model.fields:
                        if field.is_xp:
                            field.python_type = "Optional[XP]"
                            field.default = f'Field(None, alias="{field.name}")'

                # Analyse fields for import needs.
                for field in model.fields:
                    if "Optional[" in field.python_type:
                        needs_optional = True
                    if "Any" in field.python_type:
                        needs_any = True
                    if "Field(" in field.default:
                        needs_field = True

                    # Cross-module references.
                    if field.ref_type:
                        ref_module = schema_to_module.get(field.ref_type)
                        if ref_module and ref_module != module_name:
                            cross_imports.add((ref_module, field.ref_type))
                        elif field.ref_type in MANUAL_SCHEMAS:
                            cross_imports.add(("shared", field.ref_type))

        if group_enums:
            needs_enum = True

        # Detect field/type name collisions and create aliases.
        # When a field name shadows its type (e.g. Product.Inventory of
        # type Inventory), Pydantic can't resolve the forward reference.
        # Fix: create ``_Inventory = Inventory`` and use it in the annotation.
        # Imported types get aliases at module top (after imports).
        # Locally-defined types get aliases at module bottom (after the class).
        local_names = {m.name for m in group_models} | {e.name for e in group_enums}
        top_aliases: list[tuple[str, str]] = []   # imported types
        bottom_aliases: list[tuple[str, str]] = []  # locally-defined types
        alias_set: set[str] = set()
        for model in group_models:
            for field in model.fields:
                if field.ref_type and field.name == field.ref_type:
                    alias = f"_{field.ref_type}"
                    if field.ref_type not in alias_set:
                        if field.ref_type in local_names:
                            bottom_aliases.append((alias, field.ref_type))
                        else:
                            top_aliases.append((alias, field.ref_type))
                        alias_set.add(field.ref_type)
                    field.python_type = field.python_type.replace(
                        field.ref_type, alias
                    )
        type_aliases = top_aliases

        # Backward-compatibility re-exports (must precede import building).
        re_exports = RE_EXPORTS.get(module_name, [])
        for source_module, re_name in re_exports:
            cross_imports.add((source_module, re_name))

        # Build import lines.
        import_lines = _build_model_imports(
            needs_any=needs_any,
            needs_optional=needs_optional,
            needs_enum=needs_enum,
            needs_field=needs_field,
            needs_generic=needs_generic,
            needs_xp_typevar=needs_xp_typevar,
            cross_imports=cross_imports,
            has_models=bool(group_models),
        )

        # Build __all__ list.
        all_names = (
            [e.name for e in group_enums]
            + [m.name for m in group_models]
            + [re_name for _, re_name in re_exports]
        )

        # Build module docstring.
        names = [n for n in schema_names if n in models or n in enums]
        if len(names) <= 3:
            subject = ", ".join(names)
        else:
            subject = f"{names[0]} and related"
        module_docstring = f"OrderCloud {subject} models."

        groups.append(
            ModelGroup(
                module_name=module_name,
                module_docstring=module_docstring,
                models=group_models,
                enums=group_enums,
                imports=import_lines,
                all_names=all_names,
                type_aliases=type_aliases,
                type_aliases_bottom=bottom_aliases,
            )
        )

    return groups


def _build_model_imports(
    *,
    needs_any: bool,
    needs_optional: bool,
    needs_enum: bool,
    needs_field: bool,
    needs_generic: bool,
    needs_xp_typevar: bool,
    cross_imports: set[tuple[str, str]],
    has_models: bool,
) -> list[str]:
    """Build the import block for a model module."""
    lines: list[str] = []

    # Standard library — no longer needed for enums (uses OrderCloudEnum from shared).

    # Typing.
    typing_names: list[str] = []
    if needs_any:
        typing_names.append("Any")
    if needs_generic:
        typing_names.append("Generic")
    if needs_optional:
        typing_names.append("Optional")
    if typing_names:
        lines.append(f"from typing import {', '.join(sorted(typing_names))}")

    # Pydantic (only if Field is needed).
    if needs_field:
        lines.append("from pydantic import Field")

    # Blank line before relative imports.
    if lines and (cross_imports or has_models):
        lines.append("")

    # Shared base classes (OrderCloudModel for models, OrderCloudEnum for enums).
    shared_imports: list[str] = []
    if needs_enum:
        shared_imports.append("OrderCloudEnum")
    if has_models:
        shared_imports.append("OrderCloudModel")
    if needs_xp_typevar:
        shared_imports.append("XP")
    if shared_imports:
        lines.append(f"from .shared import {', '.join(sorted(shared_imports))}")

    # Cross-module imports (grouped by source module).
    by_module: dict[str, list[str]] = defaultdict(list)
    for mod, name in cross_imports:
        by_module[mod].append(name)
    for mod in sorted(by_module):
        names = sorted(by_module[mod])
        lines.append(f"from .{mod} import {', '.join(names)}")

    return lines


# ---------------------------------------------------------------------------
# Resource enrichment
# ---------------------------------------------------------------------------


def _enrich_resources(
    resources: dict[str, ResourceDef],
    enums: dict[str, EnumDef],
    schema_to_module: dict[str, str],
) -> list[ResourceDef]:
    """Compute import lines and model/enum imports for each resource."""
    enriched: list[ResourceDef] = []
    enum_names = set(enums.keys())

    for name, resource in sorted(resources.items()):
        model_refs: set[str] = set()
        enum_refs: set[str] = set()
        needs_list_page = False
        needs_meta_with_facets = False
        needs_union = False
        needs_any = False
        needs_optional = False

        for op in resource.operations:
            # Return type.
            if op.return_type:
                if op.return_type in enum_names:
                    enum_refs.add(op.return_type)
                elif op.return_type not in _SHARED_TYPES:
                    model_refs.add(op.return_type)

            if op.return_is_list:
                needs_list_page = True
                if op.uses_facet_meta:
                    needs_meta_with_facets = True

            # Body model (PATCH uses dict[str, Any], so the model isn't referenced).
            if op.body_model and op.http_method != "patch":
                if op.body_model in enum_names:
                    enum_refs.add(op.body_model)
                elif op.body_model not in _SHARED_TYPES:
                    model_refs.add(op.body_model)
                needs_union = True
                needs_any = True

            # Path params.
            for param in op.path_params:
                if param.is_enum and param.enum_type:
                    enum_refs.add(param.enum_type)

            # Query params — check for Optional, Any, and enum types.
            for param in op.query_params:
                if "Optional" in param.python_type:
                    needs_optional = True
                if "Any" in param.python_type:
                    needs_any = True
                if param.is_enum and param.enum_type:
                    enum_refs.add(param.enum_type)

            # Operations with dict body params.
            if op.body_param and not op.body_model:
                needs_any = True

            # Operations with patch (always dict[str, Any]).
            if op.http_method == "patch" and op.body_model:
                needs_any = True

        # Build import lines.
        import_lines = _build_resource_imports(
            model_refs=model_refs,
            enum_refs=enum_refs,
            needs_list_page=needs_list_page,
            needs_meta_with_facets=needs_meta_with_facets,
            needs_union=needs_union,
            needs_any=needs_any,
            needs_optional=needs_optional,
            schema_to_module=schema_to_module,
        )

        resource.model_imports = sorted(model_refs)
        resource.enum_imports = sorted(enum_refs)
        resource.import_lines = import_lines
        enriched.append(resource)

    return enriched


def _build_resource_imports(
    *,
    model_refs: set[str],
    enum_refs: set[str],
    needs_list_page: bool,
    needs_meta_with_facets: bool,
    needs_union: bool,
    needs_any: bool,
    needs_optional: bool,
    schema_to_module: dict[str, str],
) -> list[str]:
    """Build the import block for a resource module."""
    lines: list[str] = []

    # Typing.
    typing_names: list[str] = []
    if needs_any:
        typing_names.append("Any")
    if needs_optional:
        typing_names.append("Optional")
    if needs_union:
        typing_names.append("Union")
    if typing_names:
        lines.append(f"from typing import {', '.join(sorted(typing_names))}")

    # Blank line before relative imports.
    if lines:
        lines.append("")

    # Model imports — group by source module.
    by_module: dict[str, list[str]] = defaultdict(list)
    for ref in model_refs:
        mod = schema_to_module.get(ref, "misc")
        by_module[mod].append(ref)
    for ref in enum_refs:
        mod = schema_to_module.get(ref, "misc")
        by_module[mod].append(ref)

    for mod in sorted(by_module):
        names = sorted(by_module[mod])
        lines.append(f"from ..models.{mod} import {', '.join(names)}")

    # Shared imports.
    shared_names: list[str] = []
    if needs_list_page:
        shared_names.append("ListPage")
    if needs_meta_with_facets:
        shared_names.append("MetaWithFacets")
    if shared_names:
        lines.append(f"from ..models.shared import {', '.join(sorted(shared_names))}")

    # Base resource.
    lines.append("from .base import BaseResource")

    return lines
