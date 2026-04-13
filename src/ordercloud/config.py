"""OrderCloud client configuration."""

from dataclasses import dataclass, field

__all__ = ["OrderCloudConfig"]


@dataclass(frozen=True)
class OrderCloudConfig:
    """Immutable configuration for an OrderCloud API client.

    Attributes:
        client_id: OAuth2 client ID for API access.
        client_secret: OAuth2 client secret (empty for public clients).
        base_url: OrderCloud API base URL (including ``/v1``).
        auth_url: OAuth2 token endpoint URL.
        scopes: List of OAuth2 scopes to request.
        timeout: HTTP request timeout in seconds.
    """

    client_id: str
    client_secret: str = ""
    base_url: str = "https://api.ordercloud.io/v1"
    auth_url: str = "https://auth.ordercloud.io/oauth/token"
    scopes: list[str] = field(default_factory=lambda: ["FullAccess"])
    timeout: float = 30.0
