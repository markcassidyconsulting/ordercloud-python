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


class OrderCloudClient:
    """Entry point for the OrderCloud Python SDK.

    Usage::

        from ordercloud import OrderCloudClient

        async with OrderCloudClient.create(
            client_id="...",
            client_secret="...",
        ) as client:
            products = await client.products.list()
    """

    def __init__(self, config: OrderCloudConfig):
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
        await self._http.close()

    async def __aenter__(self) -> "OrderCloudClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
