# ordercloud-python

[![CI](https://github.com/markcassidyconsulting/ordercloud-python/actions/workflows/ci.yml/badge.svg)](https://github.com/markcassidyconsulting/ordercloud-python/actions/workflows/ci.yml)
[![CodeQL](https://github.com/markcassidyconsulting/ordercloud-python/actions/workflows/codeql.yml/badge.svg)](https://github.com/markcassidyconsulting/ordercloud-python/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/markcassidyconsulting/ordercloud-python/graph/badge.svg)](https://codecov.io/gh/markcassidyconsulting/ordercloud-python)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/markcassidyconsulting/ordercloud-python/badge)](https://scorecard.dev/viewer/?uri=github.com/markcassidyconsulting/ordercloud-python)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An idiomatic async Python SDK for the [Sitecore OrderCloud](https://ordercloud.io) e-commerce platform.

Built with modern Python: async/await throughout, Pydantic v2 typed models, full type annotations, and `py.typed` for downstream type checking. **Full API coverage** — all 632 operations across 60 resources, generated from the OpenAPI spec.

> **Status:** Production-grade. Full API coverage, 127 unit tests, 100% coverage on all hand-written infrastructure. Sync and async clients, typed xp generics, auto-pagination, retry with backoff, structured logging, middleware hooks.

## Why This Exists

This SDK is part of a multi-language showcase proving a thesis: **the tech no longer matters**. The same OpenAPI spec, four idiomatic SDKs (Python, Go, Rust, PHP), each built the way a practitioner of that language would build it. The platform is incidental — the skill is knowing what to build, how to validate it, and how to ship it.

## Installation

```bash
pip install ordercloud
```

Requires Python 3.10+.

## Quick Start

### Async (default)

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

### Sync

```python
from ordercloud import SyncOrderCloudClient

with SyncOrderCloudClient.create(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
) as client:
    products = client.products.list(page_size=10)
    for p in products.Items:
        print(f"{p.ID}: {p.Name}")
```

The sync client wraps the async client internally — same features, same API shape, no `await`.

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `client_id` | *(required)* | OAuth2 client ID |
| `client_secret` | `""` | OAuth2 client secret (empty for public clients) |
| `base_url` | `https://api.ordercloud.io/v1` | API base URL |
| `auth_url` | `https://auth.ordercloud.io/oauth/token` | OAuth2 token endpoint |
| `scopes` | `["FullAccess"]` | OAuth2 scopes to request |
| `timeout` | `30.0` | HTTP request timeout (seconds) |
| `max_retries` | `0` | Max retries on 429/5xx (0 = disabled) |
| `retry_backoff` | `0.5` | Base delay in seconds for exponential backoff |

### Regional Environments

| Environment | API Base URL | Auth URL |
|-------------|-------------|----------|
| US Production | `https://api.ordercloud.io/v1` | `https://auth.ordercloud.io/oauth/token` |
| US Sandbox | `https://sandboxapi.ordercloud.io/v1` | `https://sandboxauth.ordercloud.io/oauth/token` |
| Europe West Production | `https://westeurope-production.ordercloud.io/v1` | `https://westeurope-production-auth.ordercloud.io/oauth/token` |
| Europe West Sandbox | `https://westeurope-sandbox.ordercloud.io/v1` | `https://westeurope-sandbox-auth.ordercloud.io/oauth/token` |
| Australia East Production | `https://australiaeast-production.ordercloud.io/v1` | `https://australiaeast-production-auth.ordercloud.io/oauth/token` |
| Japan East Production | `https://japaneast-production.ordercloud.io/v1` | `https://japaneast-production-auth.ordercloud.io/oauth/token` |

## Typed Extended Properties (xp)

OrderCloud models support extended properties (`xp`) — arbitrary JSON attached to any resource. By default, `xp` is `dict[str, Any]`. You can type it with a Pydantic model:

```python
from pydantic import BaseModel
from ordercloud.models import Product

class MyProductXp(BaseModel):
    color: str
    weight_kg: float

# Create with typed xp
product = Product[MyProductXp](
    Name="Widget",
    xp=MyProductXp(color="red", weight_kg=1.5),
)
product.xp.color  # str, not Any

# Deserialise with typed xp
data = {"Name": "Widget", "xp": {"color": "blue", "weight_kg": 2.0}}
product = Product[MyProductXp].model_validate(data)
product.xp.color  # "blue"
```

Unparameterized usage (`Product(xp={"anything": True})`) still works — fully backward compatible.

## Auto-Pagination

Iterate through all pages automatically:

```python
from ordercloud import paginate

# Async
async for product in paginate(client.products.list, search="widget"):
    print(product.Name)

# Works with positional args too
async for order in paginate(client.orders.list, OrderDirection.Incoming):
    print(order.ID)
```

For the sync client:

```python
from ordercloud import paginate_sync

for product in paginate_sync(client.products.list, search="widget"):
    print(product.Name)
```

## Retry Logic

Enable automatic retries on transient failures (429 rate limit, 5xx server errors):

```python
client = OrderCloudClient.create(
    client_id="...",
    client_secret="...",
    max_retries=3,       # Retry up to 3 times
    retry_backoff=0.5,   # 0.5s, 1s, 2s exponential backoff
)
```

Respects `Retry-After` headers. Never retries on 4xx client errors (400, 401, 403, 404, etc.).

## Structured Logging

The SDK logs via Python's standard `logging` module under the `ordercloud` logger:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or configure just the SDK logger
logging.getLogger("ordercloud").setLevel(logging.DEBUG)
```

| Level | What's logged |
|-------|--------------|
| `DEBUG` | Every request (`Request: GET /products`) and response (`Response: GET /products 200`) |
| `WARNING` | Retry attempts with status code and backoff delay |

## Middleware Hooks

Register hooks to intercept requests and responses:

```python
from ordercloud import RequestContext, ResponseContext

async def add_correlation_id(ctx: RequestContext) -> None:
    ctx.headers["X-Correlation-ID"] = generate_id()

async def log_timing(ctx: ResponseContext) -> None:
    print(f"{ctx.request.method} {ctx.request.path} -> {ctx.response.status_code}")

client.add_before_request(add_correlation_id)
client.add_after_response(log_timing)
```

Before-request hooks receive a mutable `RequestContext` — modify `headers`, `params`, or `json` before the request is sent. After-response hooks receive a `ResponseContext` with the request details and response. Hooks are called on every attempt, including retries.

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

The codegen pipeline: **OpenAPI JSON** -> parser -> intermediate representation -> transformer -> Jinja2 templates -> Python source -> ruff format. Hand-written infrastructure (`shared.py`, `base.py`, `auth.py`, `http.py`, `config.py`, `errors.py`, `middleware.py`, `sync_client.py`) is preserved — only model and resource files are generated.

## Development

```bash
git clone https://github.com/markcassidyconsulting/ordercloud-python.git
cd ordercloud-python
pip install -e ".[dev,codegen]"

# Run linter
ruff check src/ tests/
ruff format src/ tests/

# Run tests
pytest

# Run tests with coverage
pytest --cov=ordercloud --cov-report=term-missing
```

### Test Suite

127 unit tests across 5 test modules (auth, HTTP, models, resources, sync client). All tests use mocked HTTP via `respx` — no network calls.

Coverage on hand-written infrastructure:

| Module | Coverage |
|--------|----------|
| `auth.py` | 100% |
| `client.py` | 100% |
| `config.py` | 100% |
| `errors.py` | 100% |
| `http.py` | 97% |
| `middleware.py` | 100% |
| `sync_client.py` | 100% |
| `resources/base.py` | 100% |
| `models/shared.py` | 100% |
| All 37 model modules | 100% |

## License

MIT
