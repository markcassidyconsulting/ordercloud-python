"""Naming convention helpers for the codegen pipeline.

Handles PascalCase/snake_case conversions, operationId parsing, and
the mapping from OpenAPI identifiers to Python identifiers.
"""

from __future__ import annotations

import re

__all__ = [
    "pascal_to_snake",
    "operation_id_to_method_name",
    "operation_id_to_resource_name",
    "path_param_to_snake",
    "resource_name_to_class",
    "resource_name_to_module",
    "resource_name_to_attribute",
    "path_template_to_fstring",
]


def pascal_to_snake(name: str) -> str:
    """Convert a PascalCase or camelCase name to snake_case.

    Handles consecutive uppercase letters (e.g. ``BuyerID`` → ``buyer_id``,
    ``FromUserID`` → ``from_user_id``, ``XpPath`` → ``xp_path``).

    >>> pascal_to_snake("BuyerID")
    'buyer_id'
    >>> pascal_to_snake("FromUserID")
    'from_user_id'
    >>> pascal_to_snake("ShipFromAddressID")
    'ship_from_address_id'
    >>> pascal_to_snake("LineItemCount")
    'line_item_count'
    >>> pascal_to_snake("ID")
    'id'
    >>> pascal_to_snake("xp")
    'xp'
    """
    # Insert underscore between a lowercase/digit and an uppercase letter.
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    # Insert underscore between consecutive uppercase and uppercase+lowercase.
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return s.lower()


def operation_id_to_method_name(operation_id: str) -> str:
    """Convert an operationId like ``Products.ListVariants`` to a snake_case method name.

    The resource prefix (before the dot) is stripped. The action part is
    converted from PascalCase to snake_case.

    >>> operation_id_to_method_name("Products.List")
    'list'
    >>> operation_id_to_method_name("Products.GetVariant")
    'get_variant'
    >>> operation_id_to_method_name("Orders.Submit")
    'submit'
    >>> operation_id_to_method_name("Orders.ListEligiblePromotions")
    'list_eligible_promotions'
    """
    _, _, action = operation_id.partition(".")
    return pascal_to_snake(action)


def operation_id_to_resource_name(operation_id: str) -> str:
    """Extract the resource name from an operationId.

    >>> operation_id_to_resource_name("Products.List")
    'Products'
    >>> operation_id_to_resource_name("Cart.Submit")
    'Cart'
    """
    resource, _, _ = operation_id.partition(".")
    return resource


def path_param_to_snake(param_name: str) -> str:
    """Convert an OpenAPI path parameter name to a snake_case Python identifier.

    Path params in the spec use camelCase without braces (e.g. ``buyerID``).

    >>> path_param_to_snake("buyerID")
    'buyer_id'
    >>> path_param_to_snake("orderID")
    'order_id'
    >>> path_param_to_snake("direction")
    'direction'
    >>> path_param_to_snake("catalogID")
    'catalog_id'
    """
    return pascal_to_snake(param_name)


def resource_name_to_class(resource_name: str) -> str:
    """Convert a spec resource name to a Python class name.

    >>> resource_name_to_class("Products")
    'ProductsResource'
    >>> resource_name_to_class("LineItems")
    'LineItemsResource'
    >>> resource_name_to_class("Me")
    'MeResource'
    >>> resource_name_to_class("Cart")
    'CartResource'
    """
    return f"{resource_name}Resource"


def resource_name_to_module(resource_name: str) -> str:
    """Convert a spec resource name to a snake_case module filename (no .py).

    >>> resource_name_to_module("Products")
    'products'
    >>> resource_name_to_module("LineItems")
    'line_items'
    >>> resource_name_to_module("SecurityProfiles")
    'security_profiles'
    >>> resource_name_to_module("Me")
    'me'
    """
    return pascal_to_snake(resource_name)


def resource_name_to_attribute(resource_name: str) -> str:
    """Convert a spec resource name to a snake_case client attribute.

    >>> resource_name_to_attribute("Products")
    'products'
    >>> resource_name_to_attribute("LineItems")
    'line_items'
    >>> resource_name_to_attribute("Me")
    'me'
    """
    return pascal_to_snake(resource_name)


def path_template_to_fstring(path: str, param_renames: dict[str, str] | None = None) -> str:
    """Convert an OpenAPI path template to a Python f-string.

    Replaces ``{buyerID}`` with ``{buyer_id}`` etc.

    >>> path_template_to_fstring("/buyers/{buyerID}/addresses/{addressID}")
    '/buyers/{buyer_id}/addresses/{address_id}'
    >>> path_template_to_fstring("/orders/{direction}/{orderID}/submit")
    '/orders/{direction}/{order_id}/submit'
    """
    renames = param_renames or {}

    def replace_param(match: re.Match[str]) -> str:
        original = match.group(1)
        snake = renames.get(original, path_param_to_snake(original))
        return f"{{{snake}}}"

    return re.sub(r"\{(\w+)\}", replace_param, path)
