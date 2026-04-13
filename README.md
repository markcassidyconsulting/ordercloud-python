# ordercloud-python

An idiomatic async Python SDK for the [Sitecore OrderCloud](https://ordercloud.io) e-commerce platform.

Built with modern Python: async/await throughout, Pydantic v2 typed models, full type annotations, and `py.typed` for downstream type checking.

> **Status:** Phase 1 (Foundation). The SDK covers 6 core resources with full CRUD. API coverage is expanding — see [API Coverage](#api-coverage) below.

## Why This Exists

This SDK is part of a multi-language showcase proving a thesis: **the tech no longer matters**. The same OpenAPI spec, four idiomatic SDKs (Python, Go, Rust, PHP), each built the way a practitioner of that language would build it. The platform is incidental — the skill is knowing what to build, how to validate it, and how to ship it.

## Installation

```bash
pip install ordercloud
```

Requires Python 3.10+.

## Quick Start

```python
import asyncio
from ordercloud import OrderCloudClient

async def main():
    async with OrderCloudClient.create(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
    ) as client:
        # List products
        products = await client.products.list(page_size=10)
        for p in products.Items:
            print(f"{p.ID}: {p.Name}")

        # Create a product
        from ordercloud.models import Product
        product = await client.products.create(Product(
            Name="My Product",
            Active=True,
        ))
        print(f"Created: {product.ID}")

asyncio.run(main())
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `client_id` | *(required)* | OAuth2 client ID |
| `client_secret` | `""` | OAuth2 client secret (empty for public clients) |
| `base_url` | `https://api.ordercloud.io/v1` | API base URL |
| `auth_url` | `https://auth.ordercloud.io/oauth/token` | OAuth2 token endpoint |
| `scopes` | `["FullAccess"]` | OAuth2 scopes to request |
| `timeout` | `30.0` | HTTP request timeout (seconds) |

### Regional Environments

| Environment | API Base URL | Auth URL |
|-------------|-------------|----------|
| US Production | `https://api.ordercloud.io/v1` | `https://auth.ordercloud.io/oauth/token` |
| US Sandbox | `https://sandboxapi.ordercloud.io/v1` | `https://sandboxauth.ordercloud.io/oauth/token` |
| Europe West Production | `https://westeurope-production.ordercloud.io/v1` | `https://westeurope-production-auth.ordercloud.io/oauth/token` |
| Europe West Sandbox | `https://westeurope-sandbox.ordercloud.io/v1` | `https://westeurope-sandbox-auth.ordercloud.io/oauth/token` |
| Australia East Production | `https://australiaeast-production.ordercloud.io/v1` | `https://australiaeast-production-auth.ordercloud.io/oauth/token` |
| Japan East Production | `https://japaneast-production.ordercloud.io/v1` | `https://japaneast-production-auth.ordercloud.io/oauth/token` |

## API Coverage

| Resource | list | get | create | save | patch | delete | Other |
|----------|:----:|:---:|:------:|:----:|:-----:|:------:|-------|
| Products | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | |
| Orders | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | submit, approve, cancel, complete |
| Line Items | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | |
| Catalogs | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | |
| Categories | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | |
| Buyers | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | |

Not yet implemented: Price Schedules, Specs, Suppliers, Promotions, Shipments, Payments, Security Profiles, Admin Users, User Groups, Addresses, Me endpoints, Webhooks, Incrementors.

## Usage Examples

### Products

```python
# List with search and pagination
products = await client.products.list(
    search="widget",
    search_on="Name,Description",
    sort_by="Name",
    page=1,
    page_size=20,
)
print(f"Found {products.Meta.TotalCount} products")

# Get by ID
product = await client.products.get("my-product-id")

# Create
from ordercloud.models import Product
product = await client.products.create(Product(
    ID="my-product",
    Name="Widget",
    Description="A fine widget",
    Active=True,
))

# Update (PUT — full replace)
product = await client.products.save("my-product", Product(
    Name="Updated Widget",
    Active=True,
))

# Patch (partial update)
product = await client.products.patch("my-product", {"Description": "An even finer widget"})

# Delete
await client.products.delete("my-product")
```

### Orders

```python
from ordercloud.models import Order, OrderDirection

# List incoming orders
orders = await client.orders.list(OrderDirection.Incoming, page_size=50)

# Create an outgoing order
order = await client.orders.create(
    OrderDirection.Outgoing,
    Order(Comments="Rush delivery"),
)

# Order workflow
order = await client.orders.submit(OrderDirection.Outgoing, order.ID)
order = await client.orders.approve(OrderDirection.Incoming, order.ID, comments="Approved")
order = await client.orders.complete(OrderDirection.Incoming, order.ID)
```

### Line Items

```python
from ordercloud.models import LineItem, OrderDirection

# Add a line item to an order
line_item = await client.line_items.create(
    OrderDirection.Outgoing, "order-id",
    LineItem(ProductID="my-product", Quantity=3),
)

# List line items on an order
line_items = await client.line_items.list(OrderDirection.Outgoing, "order-id")
for li in line_items.Items:
    print(f"  {li.ProductID} x{li.Quantity} = {li.LineTotal}")
```

### Catalogs and Categories

```python
from ordercloud.models import Catalog, Category

# Create a catalog
catalog = await client.catalogs.create(Catalog(
    Name="Spring Collection",
    Active=True,
))

# Create a category within it
category = await client.categories.create(catalog.ID, Category(
    Name="New Arrivals",
    Active=True,
))

# List categories (with depth control)
categories = await client.categories.list(catalog.ID, depth="all")
```

### Filtering

All `list()` methods accept a `filters` dict for server-side filtering:

```python
# Products with Active=true and Name starting with "Widget"
products = await client.products.list(filters={
    "Active": True,
    "Name": "Widget*",
})

# Orders with Total > 100
orders = await client.orders.list(filters={"Total": ">100"})
```

## Error Handling

```python
from ordercloud import OrderCloudError, AuthenticationError

try:
    product = await client.products.get("nonexistent")
except AuthenticationError as e:
    # 401 or 403
    print(f"Auth failed: {e}")
except OrderCloudError as e:
    # Any other API error (4xx/5xx)
    print(f"API error {e.status_code}: {e}")
    for error in e.errors:
        print(f"  {error.error_code}: {error.message}")
```

## Development

```bash
git clone https://github.com/markcassidyconsulting/ordercloud-python.git
cd ordercloud-python
pip install -e ".[dev]"

# Run linter
ruff check src/
ruff format src/

# Run tests (once test suite exists)
pytest
```

## License

MIT
