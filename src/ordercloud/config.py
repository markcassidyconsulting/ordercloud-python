from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrderCloudConfig:
    """Configuration for an OrderCloud API client."""

    client_id: str
    client_secret: str = ""
    base_url: str = "https://api.ordercloud.io/v1"
    auth_url: str = "https://auth.ordercloud.io/oauth/token"
    scopes: list[str] = field(default_factory=lambda: ["FullAccess"])
    timeout: float = 30.0
