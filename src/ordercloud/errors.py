"""OrderCloud API error types."""

from dataclasses import dataclass
from typing import Any, Optional

__all__ = ["ApiError", "OrderCloudError", "AuthenticationError"]


@dataclass
class ApiError:
    """A single error returned by the OrderCloud API.

    Attributes:
        error_code: Machine-readable error code (e.g. ``"NotFound"``).
        message: Human-readable error description.
        data: Optional structured data associated with the error.
    """

    error_code: str
    message: str
    data: Any = None


class OrderCloudError(Exception):
    """Raised when the OrderCloud API returns an error response.

    Attributes:
        status_code: The HTTP status code.
        errors: List of individual API errors from the response body.
        raw: The raw JSON response body, if available.
    """

    def __init__(
        self,
        status_code: int,
        errors: list[ApiError],
        raw: Optional[dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.errors = errors
        self.raw = raw
        messages = "; ".join(e.message for e in errors)
        super().__init__(f"OrderCloud {status_code}: {messages}")


class AuthenticationError(OrderCloudError):
    """Raised on 401/403 responses from the OrderCloud API."""
