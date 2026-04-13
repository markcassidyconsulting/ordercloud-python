"""OpenAPI spec parser — converts the spec JSON into raw IR.

Reads ``components/schemas`` to produce ModelDef/EnumDef objects and
``paths`` to produce ResourceDef/OperationDef objects.
"""

from __future__ import annotations

import json
import keyword
from pathlib import Path
from typing import Any

from .grouping import MANUAL_SCHEMAS
from .ir import (
    EnumDef,
    FieldDef,
    ModelDef,
    OperationDef,
    ParamDef,
    ResourceDef,
)
from .naming import (
    operation_id_to_method_name,
    operation_id_to_resource_name,
    path_param_to_snake,
    path_template_to_fstring,
    resource_name_to_attribute,
    resource_name_to_class,
    resource_name_to_module,
)
from .type_mapping import extract_ref, map_field, map_type

__all__ = ["parse_spec"]

# Query params the spec declares as arrays but the API treats as
# comma-separated strings.  Force to ``str`` to match _build_list_params.
_COMMA_SEPARATED_PARAMS = {"searchOn", "sortBy"}


def parse_spec(spec_path: Path) -> tuple[
    dict[str, ModelDef],
    dict[str, EnumDef],
    dict[str, ResourceDef],
    set[str],
]:
    """Parse an OpenAPI v3 spec into IR objects.

    Returns:
        A tuple of ``(models, enums, resources, all_schema_names)`` where
        each dict is keyed by the schema/resource name.
    """
    with open(spec_path) as f:
        spec = json.load(f)

    schemas = spec.get("components", {}).get("schemas", {})
    paths = spec.get("paths", {})

    all_schema_names = set(schemas.keys())

    enum_names: set[str] = set()
    for name, schema in schemas.items():
        if "enum" in schema and schema.get("type") == "string":
            enum_names.add(name)

    enums: dict[str, EnumDef] = {}
    models: dict[str, ModelDef] = {}

    for name, schema in schemas.items():
        if name in MANUAL_SCHEMAS:
            continue
        if name in enum_names:
            enums[name] = _parse_enum(name, schema)
        else:
            models[name] = _parse_model(name, schema, enum_names)

    resources: dict[str, ResourceDef] = {}
    _parse_paths(paths, enum_names, resources)

    return models, enums, resources, all_schema_names


# ---------------------------------------------------------------------------
# Schema parsing
# ---------------------------------------------------------------------------


def _parse_enum(name: str, schema: dict[str, Any]) -> EnumDef:
    return EnumDef(
        name=name,
        values=schema["enum"],
        description=schema.get("description", f"{name} enum."),
    )


def _parse_model(
    name: str,
    schema: dict[str, Any],
    enum_names: set[str],
) -> ModelDef:
    properties = schema.get("properties", {})
    fields: list[FieldDef] = []

    for prop_name, prop_schema in properties.items():
        read_only = prop_schema.get("readOnly", False)

        python_type, default, is_xp, is_enum_ref, is_model_ref, ref_type = (
            map_field(prop_name, prop_schema, enum_names=enum_names)
        )

        is_list = prop_schema.get("type") == "array"

        fields.append(
            FieldDef(
                name=prop_name,
                python_type=python_type,
                default=default,
                description=prop_schema.get("description", ""),
                read_only=read_only,
                is_xp=is_xp,
                is_enum_ref=is_enum_ref,
                is_model_ref=is_model_ref,
                is_list=is_list,
                ref_type=ref_type,
            )
        )

    has_xp = any(f.is_xp for f in fields)

    return ModelDef(
        name=name,
        fields=fields,
        description=schema.get("description", f"An OrderCloud {name}."),
        has_xp=has_xp,
    )


# ---------------------------------------------------------------------------
# Path parsing
# ---------------------------------------------------------------------------


def _parse_paths(
    paths: dict[str, Any],
    enum_names: set[str],
    resources: dict[str, ResourceDef],
) -> None:
    for path, methods in paths.items():
        for http_method, operation in methods.items():
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId", "")
            if not operation_id:
                continue

            resource_name = operation_id_to_resource_name(operation_id)

            if resource_name not in resources:
                resources[resource_name] = ResourceDef(
                    class_name=resource_name_to_class(resource_name),
                    module_name=resource_name_to_module(resource_name),
                    attribute_name=resource_name_to_attribute(resource_name),
                    module_docstring=f"OrderCloud {resource_name} API resource.",
                    class_docstring=f"Operations on OrderCloud {resource_name}.",
                )

            op_def = _parse_operation(path, http_method, operation, enum_names)
            resources[resource_name].operations.append(op_def)


def _parse_operation(
    path: str,
    http_method: str,
    operation: dict[str, Any],
    enum_names: set[str],
) -> OperationDef:
    operation_id = operation.get("operationId", "")
    method_name = operation_id_to_method_name(operation_id)
    summary = operation.get("summary", "")
    description = operation.get("description", "")

    path_params: list[ParamDef] = []
    query_params: list[ParamDef] = []

    for param in operation.get("parameters", []):
        param_def = _parse_param(param, enum_names)
        if param_def.location == "path":
            path_params.append(param_def)
        elif param_def.location == "query":
            query_params.append(param_def)

    body_param, body_model, required_fields = _parse_request_body(operation)
    return_type, return_is_list, uses_facet_meta = _parse_response(operation)

    fstring_path = path_template_to_fstring(path)

    return OperationDef(
        method_name=method_name,
        http_method=http_method.lower(),
        path_template=fstring_path,
        summary=summary,
        description=description,
        path_params=path_params,
        query_params=query_params,
        body_param=body_param,
        body_model=body_model,
        return_type=return_type,
        return_is_list=return_is_list,
        uses_facet_meta=uses_facet_meta,
        operation_id=operation_id,
        required_fields=required_fields,
    )


def _parse_param(
    param: dict[str, Any],
    enum_names: set[str],
) -> ParamDef:
    name = param.get("name", "")
    location = param.get("in", "query")
    required = param.get("required", location == "path")
    schema = param.get("schema", {})
    description = param.get("description", "")

    ref = extract_ref(schema)
    is_enum = ref is not None and ref in enum_names
    enum_type = ref if is_enum else None

    # The spec declares searchOn/sortBy as arrays, but the API expects
    # comma-separated strings.  Override to match _build_list_params.
    if name in _COMMA_SEPARATED_PARAMS:
        python_type = "str"
    elif is_enum and ref:
        python_type = ref
    elif ref:
        python_type = ref
    elif location == "path":
        python_type = "str"
    else:
        python_type, _ = map_type(schema)

    python_name = path_param_to_snake(name)

    # Avoid Python keywords.
    api_name_override = None
    if keyword.iskeyword(python_name):
        api_name_override = name
        python_name = f"{python_name}_"

    # Query params that are not required should be Optional.
    if location == "query" and not required:
        if not python_type.startswith("Optional["):
            python_type = f"Optional[{python_type}]"

    return ParamDef(
        name=python_name,
        python_type=python_type,
        description=description,
        location=location,
        required=required,
        is_enum=is_enum,
        enum_type=enum_type,
        api_name=api_name_override or (name if name != python_name else None),
    )


def _parse_request_body(
    operation: dict[str, Any],
) -> tuple[ParamDef | None, str | None, list[str]]:
    """Parse the request body, returning (param, model_name, required_fields)."""
    request_body = operation.get("requestBody")
    if not request_body:
        return None, None, []

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    body_schema = json_content.get("schema", {})

    if not body_schema:
        return None, None, []

    required_fields: list[str] = []
    model_name: str | None = None

    if "allOf" in body_schema:
        for item in body_schema["allOf"]:
            ref = extract_ref(item)
            if ref:
                model_name = ref
        required_fields = body_schema.get("required", [])
    else:
        ref = extract_ref(body_schema)
        if ref:
            model_name = ref
        required_fields = body_schema.get("required", [])

    if not model_name:
        param = ParamDef(
            name="body",
            python_type="dict[str, Any]",
            description="Request body.",
            location="body",
            required=True,
        )
        return param, None, required_fields

    param = ParamDef(
        name=path_param_to_snake(model_name),
        python_type=model_name,
        description=f"A ``{model_name}`` model or dict.",
        location="body",
        required=True,
    )
    return param, model_name, required_fields


def _parse_response(
    operation: dict[str, Any],
) -> tuple[str | None, bool, bool]:
    """Parse the response, returning (model_name, is_list, uses_facet_meta)."""
    responses = operation.get("responses", {})

    for status in ("200", "201"):
        resp = responses.get(status)
        if not resp:
            continue
        content = resp.get("content", {})
        json_content = content.get("application/json", {})
        resp_schema = json_content.get("schema", {})

        if not resp_schema:
            continue

        # List response pattern: {Items: T[], Meta: ...}.
        properties = resp_schema.get("properties", {})
        if "Items" in properties and "Meta" in properties:
            items_schema = properties["Items"]
            meta_schema = properties["Meta"]

            items_items = items_schema.get("items", {})
            item_ref = extract_ref(items_items)
            if not item_ref:
                item_ref = "dict[str, Any]"

            meta_ref = extract_ref(meta_schema)
            uses_facet_meta = meta_ref == "MetaWithFacets"

            return item_ref, True, uses_facet_meta

        ref = extract_ref(resp_schema)
        if ref:
            return ref, False, False

    return None, False, False
