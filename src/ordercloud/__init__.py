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

__all__ = [
    "OrderCloudClient",
    "OrderCloudConfig",
    "OrderCloudError",
    "AuthenticationError",
]
