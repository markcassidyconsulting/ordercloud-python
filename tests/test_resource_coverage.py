"""Exhaustive coverage test for all generated resource clients.

Uses introspection to discover every async method on every resource class
and calls it with synthetic arguments derived from the method signature.
The goal is coverage of the generated code paths, not correctness — that
is handled by the hand-written tests in test_resources.py.
"""

from __future__ import annotations

import enum
import inspect
import types
import typing
from typing import Any, Union, get_args, get_origin

import pytest
import respx
from httpx import Response

from ordercloud.auth import AccessToken, TokenManager
from ordercloud.config import OrderCloudConfig
from ordercloud.http import HttpClient
from ordercloud.resources.base import BaseResource

# ---------------------------------------------------------------------------
# Test configuration (matches conftest.py)
# ---------------------------------------------------------------------------

TEST_BASE_URL = "https://test-api.ordercloud.io/v1"
TEST_AUTH_URL = "https://test-auth.ordercloud.io/oauth/token"

# A universal mock response that satisfies both list and single-model parsing.
# List methods look for Items/Meta; single-model methods construct Model(**data)
# and all fields are Optional so extra keys are harmlessly absorbed (extra="allow").
UNIVERSAL_RESPONSE = {
    "ID": "test-id",
    "Items": [],
    "Meta": {
        "Page": 1,
        "PageSize": 20,
        "TotalCount": 0,
        "TotalPages": 0,
        "ItemRange": [0, 0],
    },
}


# ---------------------------------------------------------------------------
# Discover all resource classes from the client module
# ---------------------------------------------------------------------------


def _discover_resources() -> list[type[BaseResource]]:
    """Return all concrete BaseResource subclasses by importing the client module."""
    from ordercloud import client as client_mod

    resources: list[type[BaseResource]] = []
    for name in dir(client_mod):
        obj = getattr(client_mod, name)
        if isinstance(obj, type) and issubclass(obj, BaseResource) and obj is not BaseResource:
            resources.append(obj)
    return sorted(resources, key=lambda c: c.__name__)


def _is_pydantic_model(tp: Any) -> bool:
    """Check if a type annotation is a Pydantic BaseModel subclass."""
    from pydantic import BaseModel as PydanticBase

    if isinstance(tp, type) and issubclass(tp, PydanticBase):
        return True
    return False


def _is_enum_type(tp: Any) -> bool:
    """Check if a type annotation is an Enum subclass."""
    return isinstance(tp, type) and issubclass(tp, enum.Enum)


def _unwrap_optional(tp: Any) -> tuple[Any, bool]:
    """Unwrap Optional[X] or Union[X, None] to (X, True). Non-optional returns (tp, False)."""
    origin = get_origin(tp)
    if origin is Union or origin is types.UnionType:
        args = get_args(tp)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0], True
        # Union of multiple non-None types (e.g. Union[Model, dict])
        return tp, False
    return tp, False


def _resolve_arg(name: str, annotation: Any) -> Any:
    """Produce a synthetic argument value based on parameter name and type annotation.

    Rules (in priority order):
    1. `self` — skip (handled by caller)
    2. Well-known optional list params — return None (they have defaults)
    3. Parameters with `_id` suffix or containing `_id` — "test-id"
    4. Enum types — first member value
    5. Pydantic model or Union[Model, dict] — empty dict {}
    6. dict[str, Any] (partial/filters) — empty dict {}
    7. bool — False
    8. int — 1
    9. Fallback str — "test-value"
    """
    if name == "self":
        return inspect.Parameter.empty  # sentinel: skip

    # Unwrap Optional[X] to get the inner type
    inner, is_optional = _unwrap_optional(annotation)

    # If the parameter has a default (is keyword-only with Optional annotation),
    # we generally want to let defaults apply. But we need to check if it's
    # truly optional (has a default) vs required.
    # The caller sends only required params, so we handle this at call site.

    # Union types (e.g. Union[Model, dict[str, Any]])
    if get_origin(inner) is Union or (
        hasattr(types, "UnionType") and isinstance(inner, types.UnionType)
    ):
        args = get_args(inner)
        for a in args:
            if _is_pydantic_model(a):
                return {}
            if _is_enum_type(a):
                return next(iter(a))
        # Fallback for Union[X, dict]
        if any(get_origin(a) is dict or a is dict for a in args):
            return {}

    # Check the inner (unwrapped) type
    if _is_enum_type(inner):
        return next(iter(inner))

    if _is_pydantic_model(inner):
        return {}

    if inner is dict or get_origin(inner) is dict:
        return {}

    if inner is bool:
        return False

    if inner is int:
        return 1

    # String-based heuristics on parameter name
    if "_id" in name or name.endswith("_id") or name == "direction":
        # For `direction` params that are typed as OrderDirection enum,
        # this is already handled above. But if somehow it's a str:
        return "test-id"

    if name == "partial":
        return {}

    if name == "verification_code" or name == "promo_code":
        return "test-value"

    return "test-value"


def _build_args_for_method(method: Any) -> tuple[list[Any], dict[str, Any]]:
    """Inspect an async method and build positional + keyword arguments.

    Returns (positional_args, keyword_args) ready to call the method.
    Only provides values for required parameters; optional ones are left
    to their defaults.

    Uses ``typing.get_type_hints()`` to resolve stringified annotations
    (caused by ``from __future__ import annotations`` in generated code).
    """
    sig = inspect.signature(method)

    # Resolve string annotations to real types
    try:
        hints = typing.get_type_hints(method)
    except Exception:
        hints = {}

    positional: list[Any] = []
    keyword: dict[str, Any] = {}

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        # Prefer resolved hint; fall back to raw annotation
        annotation = hints.get(param_name, param.annotation)
        if annotation is inspect.Parameter.empty:
            annotation = str  # assume string

        # Determine if the parameter is required
        has_default = param.default is not inspect.Parameter.empty

        if has_default:
            # Skip optional params — let defaults apply
            continue

        value = _resolve_arg(param_name, annotation)

        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            positional.append(value)
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            keyword[param_name] = value

    return positional, keyword


def _discover_methods(resource_cls: type[BaseResource]) -> list[str]:
    """Return the names of all public async methods on a resource class."""
    methods: list[str] = []
    for name in sorted(dir(resource_cls)):
        if name.startswith("_"):
            continue
        attr = getattr(resource_cls, name)
        if inspect.iscoroutinefunction(attr):
            methods.append(name)
    return methods


# ---------------------------------------------------------------------------
# Collect test cases: (resource_class, method_name) pairs
# ---------------------------------------------------------------------------

_ALL_RESOURCES = _discover_resources()
_TEST_CASES: list[tuple[type[BaseResource], str]] = []
for _res_cls in _ALL_RESOURCES:
    for _method_name in _discover_methods(_res_cls):
        _TEST_CASES.append((_res_cls, _method_name))


def _test_id(case: tuple[type[BaseResource], str]) -> str:
    """Readable test ID: ResourceName.method_name"""
    return f"{case[0].__name__}.{case[1]}"


# ---------------------------------------------------------------------------
# The test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "resource_cls,method_name", _TEST_CASES, ids=[_test_id(c) for c in _TEST_CASES]
)
async def test_resource_method_executes(resource_cls: type[BaseResource], method_name: str) -> None:
    """Call every async method on every resource with synthetic args.

    Uses a catch-all respx route so any HTTP request returns a universal
    response that satisfies both list and single-model parsing.
    """
    # Build a standalone HttpClient with pre-populated auth token
    config = OrderCloudConfig(
        client_id="test-client-id",
        client_secret="test-client-secret",
        base_url=TEST_BASE_URL,
        auth_url=TEST_AUTH_URL,
        scopes=["FullAccess"],
        timeout=5.0,
    )
    token_manager = TokenManager(config)
    http = HttpClient(config, token_manager)
    token_manager._token = AccessToken("mock-token-12345", expires_in=600)

    try:
        resource = resource_cls(http)
        method = getattr(resource, method_name)
        pos_args, kw_args = _build_args_for_method(method)

        async with respx.mock(assert_all_called=False) as router:
            # Catch-all route for any request
            router.route().mock(return_value=Response(200, json=UNIVERSAL_RESPONSE))

            await method(*pos_args, **kw_args)
            # No assertion on result — we just verify it didn't raise
    finally:
        await http.close()
