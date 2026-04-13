"""Idiomatic Python SDK for Sitecore OrderCloud.

Quick start::

    from ordercloud import OrderCloudClient

    async with OrderCloudClient.create(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
    ) as client:
        products = await client.products.list()
"""

from .client import OrderCloudClient
from .config import OrderCloudConfig
from .errors import AuthenticationError, OrderCloudError
from .middleware import AfterResponse, BeforeRequest, RequestContext, ResponseContext
from .resources.base import paginate
from .sync_client import SyncOrderCloudClient, paginate_sync

__all__ = [
    "OrderCloudClient",
    "SyncOrderCloudClient",
    "OrderCloudConfig",
    "OrderCloudError",
    "AuthenticationError",
    "BeforeRequest",
    "AfterResponse",
    "RequestContext",
    "ResponseContext",
    "paginate",
    "paginate_sync",
]
