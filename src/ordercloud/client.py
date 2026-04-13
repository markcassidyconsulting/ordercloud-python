"""OrderCloud SDK client — the main entry point."""

from typing import Optional

from .auth import TokenManager
from .config import OrderCloudConfig
from .http import HttpClient
from .resources.buyers import BuyersResource
from .resources.catalogs import CatalogsResource
from .resources.categories import CategoriesResource
from .resources.line_items import LineItemsResource
from .resources.orders import OrdersResource
from .resources.products import ProductsResource

__all__ = ["OrderCloudClient"]


class OrderCloudClient:
    """Entry point for the OrderCloud Python SDK.

    Provides access to all OrderCloud API resources as attributes.
    Use the ``create`` class method for convenient construction, or
    pass an ``OrderCloudConfig`` directly.

    Example::

        async with OrderCloudClient.create(
            client_id="...",
            client_secret="...",
        ) as client:
            products = await client.products.list()

    Attributes:
        products: Product operations.
        catalogs: Catalog operations.
        categories: Category operations (nested under catalogs).
        buyers: Buyer operations.
        orders: Order operations.
        line_items: Line item operations (nested under orders).
    """

    def __init__(self, config: OrderCloudConfig) -> None:
        self._config = config
        self._token_manager = TokenManager(config)
        self._http = HttpClient(config, self._token_manager)

        self.products = ProductsResource(self._http)
        self.catalogs = CatalogsResource(self._http)
        self.categories = CategoriesResource(self._http)
        self.buyers = BuyersResource(self._http)
        self.orders = OrdersResource(self._http)
        self.line_items = LineItemsResource(self._http)

    @classmethod
    def create(
        cls,
        client_id: str,
        client_secret: str = "",
        *,
        base_url: str = "https://api.ordercloud.io/v1",
        auth_url: str = "https://auth.ordercloud.io/oauth/token",
        scopes: Optional[list[str]] = None,
        timeout: float = 30.0,
    ) -> "OrderCloudClient":
        """Create a client with individual configuration parameters.

        This is a convenience alternative to constructing an
        ``OrderCloudConfig`` manually.

        Args:
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret (empty for public clients).
            base_url: API base URL including ``/v1``.
            auth_url: OAuth2 token endpoint URL.
            scopes: OAuth2 scopes to request (defaults to ``["FullAccess"]``).
            timeout: HTTP request timeout in seconds.

        Returns:
            A configured ``OrderCloudClient`` instance.
        """
        config = OrderCloudConfig(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            auth_url=auth_url,
            scopes=scopes or ["FullAccess"],
            timeout=timeout,
        )
        return cls(config)

    async def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        await self._http.close()

    async def __aenter__(self) -> "OrderCloudClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
