"""Integration test configuration and fixtures.

These tests run against a live OrderCloud sandbox. They are skipped
automatically when credentials are not available in the environment.

Required environment variables (typically in .env at repo root):
    ORDERCLOUD_CLIENT_ID
    ORDERCLOUD_CLIENT_SECRET
    ORDERCLOUD_BASE_URL  (optional, defaults to US production)
    ORDERCLOUD_AUTH_URL   (optional, defaults to US production)
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import pytest

from ordercloud import (
    OrderCloudClient,
    OrderCloudConfig,
    OrderCloudError,
    SyncOrderCloudClient,
)

# ---------------------------------------------------------------------------
# Load credentials
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv

    _repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
    load_dotenv(os.path.join(_repo_root, ".env"))
except ImportError:
    pass  # dotenv not installed — rely on env vars being set directly

HAS_CREDENTIALS = bool(
    os.environ.get("ORDERCLOUD_CLIENT_ID") and os.environ.get("ORDERCLOUD_CLIENT_SECRET")
)


def _make_config(**overrides: object) -> OrderCloudConfig:
    """Build OrderCloudConfig from environment variables."""
    kwargs: dict = {
        "client_id": os.environ["ORDERCLOUD_CLIENT_ID"],
        "client_secret": os.environ["ORDERCLOUD_CLIENT_SECRET"],
        "base_url": os.environ.get("ORDERCLOUD_BASE_URL", "https://api.ordercloud.io/v1"),
        "auth_url": os.environ.get("ORDERCLOUD_AUTH_URL", "https://auth.ordercloud.io/oauth/token"),
        "max_retries": 2,
        "retry_backoff": 1.0,
    }
    kwargs.update(overrides)
    return OrderCloudConfig(**kwargs)


# ---------------------------------------------------------------------------
# Skip logic
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _require_credentials() -> None:
    """Skip every integration test when sandbox credentials are absent."""
    if not HAS_CREDENTIALS:
        pytest.skip("OrderCloud sandbox credentials not available")


# ---------------------------------------------------------------------------
# Configuration & clients
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def oc_config() -> OrderCloudConfig:
    """Live sandbox configuration."""
    if not HAS_CREDENTIALS:
        pytest.skip("OrderCloud sandbox credentials not available")
    return _make_config()


@pytest.fixture
async def async_client(oc_config: OrderCloudConfig) -> OrderCloudClient:  # type: ignore[misc]
    """Function-scoped async client — one per test."""
    async with OrderCloudClient(oc_config) as client:
        yield client  # type: ignore[misc]


@pytest.fixture(scope="module")
def sync_client(oc_config: OrderCloudConfig) -> SyncOrderCloudClient:  # type: ignore[misc]
    """Module-scoped sync client for setup/teardown and sync tests."""
    with SyncOrderCloudClient(oc_config) as client:
        yield client  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def safe_delete(fn: object, *args: object, **kwargs: object) -> None:
    """Call a sync delete function, swallowing 404 (already gone)."""
    try:
        fn(*args, **kwargs)  # type: ignore[operator]
    except OrderCloudError as exc:
        if exc.status_code != 404:
            raise


async def async_safe_delete(coro: object) -> None:
    """Await a delete coroutine, swallowing 404 (already gone)."""
    try:
        await coro  # type: ignore[misc]
    except OrderCloudError as exc:
        if exc.status_code != 404:
            raise


async def wait_for_listed(
    list_fn: Any,
    expected_id: str,
    *args: Any,
    timeout: float = 10.0,
    interval: float = 1.0,
    **kwargs: Any,
) -> Any:
    """Retry a list call until the expected item appears in results.

    OrderCloud product search uses eventually-consistent indexing.
    Newly created items may not appear in list/filter queries for
    several seconds.  This helper polls until the item shows up or
    the timeout expires.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    page = None
    while asyncio.get_event_loop().time() < deadline:
        page = await list_fn(*args, **kwargs)
        if any(getattr(item, "ID", None) == expected_id for item in page.Items):
            return page
        await asyncio.sleep(interval)
    return page


def wait_for_listed_sync(
    list_fn: Any,
    expected_id: str,
    *args: Any,
    timeout: float = 10.0,
    interval: float = 1.0,
    **kwargs: Any,
) -> Any:
    """Sync version of wait_for_listed."""
    deadline = time.time() + timeout
    page = None
    while time.time() < deadline:
        page = list_fn(*args, **kwargs)
        if any(getattr(item, "ID", None) == expected_id for item in page.Items):
            return page
        time.sleep(interval)
    return page


async def async_cleanup_buyer(client: OrderCloudClient, buyer_id: str) -> None:
    """Delete a buyer and its auto-created default catalog.

    OrderCloud auto-creates a catalog with the buyer's ID when a buyer
    is created.  Deleting the buyer does not remove the catalog, so we
    clean up both.  Order matters: buyer first, then the orphaned catalog.
    """
    await async_safe_delete(client.buyers.delete(buyer_id))
    await async_safe_delete(client.catalogs.delete(buyer_id))


def sync_cleanup_buyer(client: SyncOrderCloudClient, buyer_id: str) -> None:
    """Sync version of async_cleanup_buyer."""
    safe_delete(client.buyers.delete, buyer_id)
    safe_delete(client.catalogs.delete, buyer_id)


# ---------------------------------------------------------------------------
# Shared test data (module-scoped, created via sync client)
# ---------------------------------------------------------------------------

TEST_BUYER_ID = "inttest-buyer"
TEST_CATALOG_ID = "inttest-catalog"
TEST_USER_ID = "inttest-user"


@pytest.fixture(scope="module")
def test_buyer(sync_client: SyncOrderCloudClient):  # type: ignore[misc]
    """A buyer that persists for the test module."""
    # Clean up orphaned auto-catalog from previous failed runs
    safe_delete(sync_client.catalogs.delete, TEST_BUYER_ID)
    buyer = sync_client.buyers.save(
        TEST_BUYER_ID,
        {"ID": TEST_BUYER_ID, "Name": "Integration Test Buyer", "Active": True},
    )
    yield buyer
    sync_cleanup_buyer(sync_client, TEST_BUYER_ID)


@pytest.fixture(scope="module")
def test_catalog(sync_client: SyncOrderCloudClient):  # type: ignore[misc]
    """A catalog that persists for the test module."""
    catalog = sync_client.catalogs.save(
        TEST_CATALOG_ID,
        {"ID": TEST_CATALOG_ID, "Name": "Integration Test Catalog", "Active": True},
    )
    yield catalog
    safe_delete(sync_client.catalogs.delete, TEST_CATALOG_ID)


@pytest.fixture(scope="module")
def test_user(sync_client: SyncOrderCloudClient, test_buyer: object):  # type: ignore[misc]
    """A user under the test buyer, persists for the test module."""
    user = sync_client.users.save(
        TEST_BUYER_ID,
        TEST_USER_ID,
        {
            "ID": TEST_USER_ID,
            "Username": "inttest-user",
            "FirstName": "Integration",
            "LastName": "Test",
            "Email": "inttest@example.com",
            "Active": True,
        },
    )
    yield user
    safe_delete(sync_client.users.delete, TEST_BUYER_ID, TEST_USER_ID)
