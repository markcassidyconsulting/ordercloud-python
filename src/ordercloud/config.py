"""OrderCloud client configuration."""

from dataclasses import dataclass

__all__ = ["OrderCloudConfig"]


@dataclass(frozen=True)
class OrderCloudConfig:
    """Immutable configuration for an OrderCloud API client.

    Attributes:
        client_id: OAuth2 client ID for API access.
        client_secret: OAuth2 client secret (empty for public clients).
        base_url: OrderCloud API base URL (including ``/v1``).
        auth_url: OAuth2 token endpoint URL.
        scopes: OAuth2 scopes to request (converted to tuple for immutability).
        timeout: HTTP request timeout in seconds.
        max_retries: Maximum number of retries on 429/5xx responses (0 = disabled).
        retry_backoff: Base delay in seconds for exponential backoff between retries.
    """

    client_id: str
    client_secret: str = ""
    base_url: str = "https://api.ordercloud.io/v1"
    auth_url: str = "https://auth.ordercloud.io/oauth/token"
    scopes: tuple[str, ...] = ("FullAccess",)
    timeout: float = 30.0
    max_retries: int = 0
    retry_backoff: float = 0.5

    def __post_init__(self) -> None:
        if not isinstance(self.scopes, tuple):
            object.__setattr__(self, "scopes", tuple(self.scopes))

    def __repr__(self) -> str:
        return (
            f"OrderCloudConfig(client_id={self.client_id!r}, "
            f"client_secret='***', "
            f"base_url={self.base_url!r}, "
            f"auth_url={self.auth_url!r})"
        )
