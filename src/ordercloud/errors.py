from dataclasses import dataclass
from typing import Optional


@dataclass
class ApiError:
    """A single error returned by the OrderCloud API."""

    error_code: str
    message: str
    data: object = None


class OrderCloudError(Exception):
    """Raised when the OrderCloud API returns an error response."""

    def __init__(self, status_code: int, errors: list[ApiError], raw: Optional[dict] = None):
        self.status_code = status_code
        self.errors = errors
        self.raw = raw
        messages = "; ".join(e.message for e in errors)
        super().__init__(f"OrderCloud {status_code}: {messages}")


class AuthenticationError(OrderCloudError):
    """Raised on 401/403 responses."""
