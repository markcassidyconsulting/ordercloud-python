# ordercloud-python

An idiomatic async Python SDK for the [Sitecore OrderCloud](https://ordercloud.io) e-commerce platform.

Built with modern Python: async/await throughout, Pydantic v2 typed models, full type annotations, and `py.typed` for downstream type checking. **Full API coverage** — all 632 operations across 60 resources, generated from the OpenAPI spec.

> **Status:** Phase 2 (Full API Coverage). Models and resources are generated from the official OpenAPI v3 spec via an included codegen tool. The SDK covers all OrderCloud API endpoints.

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

The SDK covers **all 60 resources** and **632 operations** in the OrderCloud API. Models and resource clients are generated from the official OpenAPI v3 spec (version 1.0.445).

### Core Commerce

| Resource | Operations | Highlights |
|----------|-----------|------------|
| Products | 18 | CRUD, variants, specs, suppliers, assignments |
| Orders | 29 | CRUD, submit, approve, decline, cancel, complete, forward, split, ship, promotions |
| Line Items | 9 | CRUD, shipping address management, cross-order listing |
| Cart | 37 | Full shopping cart lifecycle, checkout, payments, promotions |
| Bundles | 12 | CRUD, product/catalog assignments |
| Catalogs | 15 | CRUD, product/bundle/category assignments |
| Categories | 15 | CRUD, hierarchical with depth control, assignments |

### Buyers & Users

| Resource | Operations | Highlights |
|----------|-----------|------------|
| Buyers | 7 | CRUD, seller relationships |
| Buyer Groups | 6 | CRUD |
| Users | 11 | CRUD, access tokens, move, cross-buyer listing |
| User Groups | 9 | CRUD, user assignments |
| Me | 80 | Full buyer-perspective API (addresses, orders, products, subscriptions, etc.) |
| Admin Users | 8 | CRUD, token revocation, account unlock |
| Admin User Groups | 9 | CRUD, user assignments |

### Pricing & Promotions

| Resource | Operations | Highlights |
|----------|-----------|------------|
| Price Schedules | 8 | CRUD, price breaks |
| Promotions | 9 | CRUD, assignments |
| Discounts | 9 | CRUD, assignments |
| Specs | 15 | CRUD, options, product assignments |

### Fulfillment

| Resource | Operations | Highlights |
|----------|-----------|------------|
| Shipments | 12 | CRUD, items, ship-from/ship-to addresses |
| Payments | 7 | CRUD, transactions |
| Order Returns | 14 | CRUD, submit, approve, decline, complete, cancel |

### Organisation & Security

| Resource | Operations | Highlights |
|----------|-----------|------------|
| Suppliers | 9 | CRUD, buyer relationships |
| Security Profiles | 9 | CRUD, assignments |
| API Clients | 15 | CRUD, secrets, assignments |
| Addresses | 9 | CRUD, assignments |
| Cost Centers | 9 | CRUD, assignments |
| Credit Cards | 9 | CRUD, assignments |
| Spending Accounts | 9 | CRUD, assignments |

### Integrations & Infrastructure

| Resource | Operations | Highlights |
|----------|-----------|------------|
| Webhooks | 6 | CRUD |
| Integration Events | 10 | CRUD, calculate, estimate shipping |
| Message Senders | 11 | CRUD, assignments, CC listeners |
| Subscriptions | 6 | CRUD |
| Entity Syncs | 40 | Full sync infrastructure |
| Delivery Configurations | 6 | CRUD |
| Inventory Records | 18 | CRUD, variant records, assignments |

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
order = await client.orders.approve(OrderDirection.Incoming, order.ID)
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
    print(f"  {li.ProductID} x{li.Quantity}")
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

## Code Generation

Models and resource clients are generated from the OrderCloud OpenAPI v3 spec using the included codegen tool:

```bash
pip install -e ".[codegen]"
python -m tools.codegen --spec path/to/ordercloud-openapi-v3.json --output src/ordercloud
```

The codegen pipeline: **OpenAPI JSON** → parser → intermediate representation → transformer → Jinja2 templates → Python source → ruff format. Hand-written infrastructure (`shared.py`, `base.py`, `auth.py`, `http.py`, `config.py`, `errors.py`) is preserved — only model and resource files are generated.

## Development

```bash
git clone https://github.com/markcassidyconsulting/ordercloud-python.git
cd ordercloud-python
pip install -e ".[dev,codegen]"

# Run linter
ruff check src/
ruff format src/

# Run tests (once test suite exists)
pytest
```

## License

MIT
