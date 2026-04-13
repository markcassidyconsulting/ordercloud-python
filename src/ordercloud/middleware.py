"""Middleware hook types for intercepting HTTP requests and responses."""

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

import httpx

__all__ = [
    "RequestContext",
    "ResponseContext",
    "BeforeRequest",
    "AfterResponse",
]


@dataclass
class RequestContext:
    """Mutable context passed to before-request hooks.

    Hooks can modify ``headers``, ``params``, or ``json`` in place
    before the request is sent.

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
