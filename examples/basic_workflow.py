"""Basic OrderCloud workflow: authenticate, create a product, list products, get by ID."""

import asyncio
import os

from dotenv import load_dotenv

# Add src to path for development
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ordercloud import OrderCloudClient

load_dotenv()


async def main():
    client_id = os.environ["ORDERCLOUD_CLIENT_ID"]
    client_secret = os.environ["ORDERCLOUD_CLIENT_SECRET"]

    base_url = os.environ.get("ORDERCLOUD_BASE_URL", "https://api.ordercloud.io/v1")
    auth_url = os.environ.get("ORDERCLOUD_AUTH_URL", "https://auth.ordercloud.io/oauth/token")

    async with OrderCloudClient.create(
        client_id=client_id,
        client_secret=client_secret,
        base_url=base_url,
        auth_url=auth_url,
    ) as oc:
        # Create or update a product (Save = PUT, idempotent)
        product = await oc.products.save(
            "sdk-demo-001",
            {
                "ID": "sdk-demo-001",
                "Name": "SDK Demo Product",
                "Description": "Created by the OrderCloud Python SDK",
                "Active": True,
                "QuantityMultiplier": 1,
            },
        )
        print(f"Saved: {product.id} — {product.name}")

        # List all products
        products = await oc.products.list(page_size=10)
        print(f"Total products: {products.meta.total_count}")
        for p in products.items:
            print(f"  {p.id}: {p.name}")

        # Get by ID
        fetched = await oc.products.get("sdk-demo-001")
        print(f"Fetched: {fetched.id} — {fetched.description}")

        # Clean up
        await oc.products.delete("sdk-demo-001")
        print("Deleted sdk-demo-001")


if __name__ == "__main__":
    asyncio.run(main())
