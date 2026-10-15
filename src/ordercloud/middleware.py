"""Middleware hook types for intercepting HTTP requests and responses."""

import reprlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

import httpx

__all__ = [
    "RequestContext",
    "ResponseContext",
    "BeforeRequest",
    "AfterResponse",
]

_REDACTED = "***"


def _is_authorization(key: object) -> bool:
    # httpx accepts bytes header names as well as str.
    if isinstance(key, bytes):
        key = key.decode("latin-1")
    return isinstance(key, str) and key.lower() == "authorization"


def _redacted_headers_repr(headers: object) -> str:
    """Render ``headers`` as a dict repr with every ``Authorization`` value as ``'***'``."""
    # A repr must never raise or leak, so anything that is not a mapping, or
    # cannot be rendered, is shown as '***' whole rather than by its own repr.
    try:
        if not isinstance(headers, Mapping):
            return repr(_REDACTED)
        entries = []
        for key, value in list(headers.items()):
            shown = _REDACTED if _is_authorization(key) else value
            entries.append(f"{key!r}: {shown!r}")
        return "{" + ", ".join(entries) + "}"
    except Exception:
        return repr(_REDACTED)


@dataclass(repr=False)
class RequestContext:
    """Mutable context passed to before-request hooks.

    Hooks can modify ``headers``, ``params``, or ``json`` in place
    before the request is sent.

    ``path``, ``url`` and ``params`` are the concrete values sent on the
    wire, and ``headers`` holds the ``Authorization`` bearer token. Any of
    them may carry credentials: a password-reset verification code or a
    group-order invitation ID in the path, for example. ``repr()`` and
    ``str()`` of the context render the ``Authorization`` header's value as
    ``***``, but ``path``, ``url``, ``params``, ``json`` and the ``headers``
    dict itself hold the concrete values, so a hook that logs those must
    redact them itself. The SDK's own log lines redact such path values.

    Attributes:
        method: HTTP method (e.g. ``"GET"``).
        path: API path relative to the base URL.
        url: Fully resolved request URL.
        headers: Request headers (mutable).
        params: Query parameters (mutable, may be ``None``).
        json: JSON request body (mutable, may be ``None``).
    """

    method: str
    path: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: Optional[dict[str, Any]] = None
    json: Optional[dict[str, Any]] = None

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        return (
            f"{type(self).__qualname__}("
            f"method={self.method!r}, "
            f"path={self.path!r}, "
            f"url={self.url!r}, "
            f"headers={_redacted_headers_repr(self.headers)}, "
            f"params={self.params!r}, "
            f"json={self.json!r})"
        )


@dataclass
class ResponseContext:
    """Context passed to after-response hooks.

    Attributes:
        request: The request context that produced this response.
        response: The HTTP response.
        attempt: Zero-based attempt number (0 on first try, >0 on retries).
    """

    request: RequestContext
    response: httpx.Response
    attempt: int


BeforeRequest = Callable[[RequestContext], Awaitable[None]]
"""Async callable invoked before each HTTP request.

Receives a mutable ``RequestContext`` — modify it to alter headers,
params, or the JSON body before the request is sent.
"""

AfterResponse = Callable[[ResponseContext], Awaitable[None]]
"""Async callable invoked after each HTTP response (including retries).

Receives a ``ResponseContext`` with the request details and the response.
"""
