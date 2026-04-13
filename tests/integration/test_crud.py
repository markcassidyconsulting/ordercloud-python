"""Integration tests: CRUD lifecycle for representative resources.

Each test class covers one resource type with a full create -> get ->
patch -> list -> delete -> verify-404 lifecycle.
"""

from __future__ import annotations

import pytest

from ordercloud import OrderCloudClient, OrderCloudError
from ordercloud.models.product import Product

from .conftest import async_cleanup_buyer, async_safe_delete, wait_for_listed


# ---------------------------------------------------------------------------
# Products — no dependencies
# ---------------------------------------------------------------------------


class TestProductCRUD:
    """Product lifecycle: save -> get -> patch -> list -> delete."""

    PID = "inttest-prod-crud"

    async def test_product_lifecycle(self, async_client: OrderCloudClient) -> None:
        # Pre-cleanup from any prior failed run
        await async_safe_delete(async_client.products.delete(self.PID))

        # Create (via save = PUT, idempotent)
        product = await async_client.products.save(
            self.PID, {"ID": self.PID, "Name": "Integration Test Product", "Active": True}
        )
        assert product.id == self.PID
        assert product.name == "Integration Test Product"
        assert isinstance(product, Product)

        # Get
        fetched = await async_client.products.get(self.PID)
        assert fetched.id == self.PID
        assert fetched.name == "Integration Test Product"

        # Patch
        updated = await async_client.products.patch(self.PID, {"Name": "Updated Product"})
        assert updated.name == "Updated Product"

        # Verify patch persisted
        refetched = await async_client.products.get(self.PID)
        assert refetched.name == "Updated Product"

        # List with filter (product search index is eventually consistent)
        page = await wait_for_listed(async_client.products.list, self.PID, filters={"ID": self.PID})
        assert page.meta.total_count >= 1
        assert any(p.id == self.PID for p in page.items)

        # Delete (product GET may lag behind due to eventual consistency,
        # so delete-then-404 is verified on non-product resources below
        # and in test_errors.py)
        await async_client.products.delete(self.PID)

    async def test_create_with_model_object(self, async_client: OrderCloudClient) -> None:
        """Passing a Pydantic model (not just a dict) works correctly."""
        pid = "inttest-prod-model"
        await async_safe_delete(async_client.products.delete(pid))

        model = Product(ID=pid, Name="Model Test Product", Active=True)
        created = await async_client.products.save(pid, model)
        assert created.id == pid
        assert created.name == "Model Test Product"

        await async_client.products.delete(pid)

    async def test_xp_round_trip(self, async_client: OrderCloudClient) -> None:
        """Extended properties (xp) survive a create/get round-trip."""
        pid = "inttest-prod-xp"
        await async_safe_delete(async_client.products.delete(pid))

        await async_client.products.save(
            pid,
            {
                "ID": pid,
                "Name": "XP Test Product",
                "Active": True,
                "xp": {"custom_field": "hello", "nested": {"key": 42}},
            },
        )
        fetched = await async_client.products.get(pid)
        assert fetched.xp is not None
        assert fetched.xp["custom_field"] == "hello"
        assert fetched.xp["nested"]["key"] == 42

        await async_client.products.delete(pid)


# ---------------------------------------------------------------------------
# Buyers — auto-creates a default catalog with the buyer ID
# ---------------------------------------------------------------------------


class TestBuyerCRUD:
    """Buyer lifecycle: save -> get -> patch -> list -> delete."""

    BID = "inttest-buyer-crud"

    async def test_buyer_lifecycle(self, async_client: OrderCloudClient) -> None:
        # Pre-cleanup: buyer + its auto-created catalog
        await async_cleanup_buyer(async_client, self.BID)

        buyer = await async_client.buyers.save(
            self.BID, {"ID": self.BID, "Name": "Integration Test Buyer", "Active": True}
        )
        assert buyer.id == self.BID
        assert buyer.name == "Integration Test Buyer"

        fetched = await async_client.buyers.get(self.BID)
        assert fetched.id == self.BID

        updated = await async_client.buyers.patch(self.BID, {"Name": "Updated Buyer"})
        assert updated.name == "Updated Buyer"

        page = await async_client.buyers.list(filters={"ID": self.BID})
        assert page.meta.total_count >= 1
        assert any(b.id == self.BID for b in page.items)

        # Cleanup
        await async_cleanup_buyer(async_client, self.BID)

        with pytest.raises(OrderCloudError) as exc_info:
            await async_client.buyers.get(self.BID)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Catalogs — no dependencies
# ---------------------------------------------------------------------------


class TestCatalogCRUD:
    """Catalog lifecycle: save -> get -> patch -> list -> delete."""

    CID = "inttest-catalog-crud"

    async def test_catalog_lifecycle(self, async_client: OrderCloudClient) -> None:
        await async_safe_delete(async_client.catalogs.delete(self.CID))

        catalog = await async_client.catalogs.save(
            self.CID, {"ID": self.CID, "Name": "Integration Test Catalog", "Active": True}
        )
        assert catalog.id == self.CID
        assert catalog.name == "Integration Test Catalog"

        fetched = await async_client.catalogs.get(self.CID)
        assert fetched.name == "Integration Test Catalog"

        updated = await async_client.catalogs.patch(self.CID, {"Name": "Updated Catalog"})
        assert updated.name == "Updated Catalog"

        page = await async_client.catalogs.list(filters={"ID": self.CID})
        assert page.meta.total_count >= 1
        assert any(c.id == self.CID for c in page.items)

        await async_client.catalogs.delete(self.CID)

        with pytest.raises(OrderCloudError) as exc_info:
            await async_client.catalogs.get(self.CID)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Categories — requires a catalog
# ---------------------------------------------------------------------------


class TestCategoryCRUD:
    """Category lifecycle under a temporary catalog."""

    CATALOG_ID = "inttest-catalog-for-cat"
    CAT_ID = "inttest-category-crud"

    async def test_category_lifecycle(self, async_client: OrderCloudClient) -> None:
        # Pre-cleanup
        await async_safe_delete(async_client.categories.delete(self.CATALOG_ID, self.CAT_ID))
        await async_safe_delete(async_client.catalogs.delete(self.CATALOG_ID))

        # Create the parent catalog
        await async_client.catalogs.save(
            self.CATALOG_ID,
            {"ID": self.CATALOG_ID, "Name": "Catalog for Category Tests", "Active": True},
        )

        category = await async_client.categories.create(
            self.CATALOG_ID,
            {"ID": self.CAT_ID, "Name": "Test Category", "Active": True},
        )
        assert category.id == self.CAT_ID
        assert category.name == "Test Category"

        fetched = await async_client.categories.get(self.CATALOG_ID, self.CAT_ID)
        assert fetched.name == "Test Category"

        updated = await async_client.categories.patch(
            self.CATALOG_ID, self.CAT_ID, {"Name": "Updated Category"}
        )
        assert updated.name == "Updated Category"

        page = await async_client.categories.list(self.CATALOG_ID)
        assert page.meta.total_count >= 1
        assert any(c.id == self.CAT_ID for c in page.items)

        # Delete the category
        await async_client.categories.delete(self.CATALOG_ID, self.CAT_ID)

        with pytest.raises(OrderCloudError) as exc_info:
            await async_client.categories.get(self.CATALOG_ID, self.CAT_ID)
        assert exc_info.value.status_code == 404

        # Cleanup parent catalog
        await async_client.catalogs.delete(self.CATALOG_ID)


# ---------------------------------------------------------------------------
# Users — requires a buyer
# ---------------------------------------------------------------------------


class TestUserCRUD:
    """User lifecycle under a temporary buyer."""

    BUYER_ID = "inttest-buyer-for-user"
    UID = "inttest-user-crud"

    async def test_user_lifecycle(self, async_client: OrderCloudClient) -> None:
        # Pre-cleanup
        await async_safe_delete(async_client.users.delete(self.BUYER_ID, self.UID))
        await async_cleanup_buyer(async_client, self.BUYER_ID)

        # Create the parent buyer
        await async_client.buyers.save(
            self.BUYER_ID,
            {"ID": self.BUYER_ID, "Name": "Buyer for User Tests", "Active": True},
        )

        user = await async_client.users.save(
            self.BUYER_ID,
            self.UID,
            {
                "ID": self.UID,
                "Username": "inttest-user-crud",
                "FirstName": "Test",
                "LastName": "User",
                "Email": "test-user-crud@example.com",
                "Active": True,
            },
        )
        assert user.id == self.UID
        assert user.username == "inttest-user-crud"

        fetched = await async_client.users.get(self.BUYER_ID, self.UID)
        assert fetched.first_name == "Test"

        updated = await async_client.users.patch(self.BUYER_ID, self.UID, {"FirstName": "Updated"})
        assert updated.first_name == "Updated"

        page = await async_client.users.list(self.BUYER_ID)
        assert page.meta.total_count >= 1
        assert any(u.id == self.UID for u in page.items)

        await async_client.users.delete(self.BUYER_ID, self.UID)

        with pytest.raises(OrderCloudError) as exc_info:
            await async_client.users.get(self.BUYER_ID, self.UID)
        assert exc_info.value.status_code == 404

        # Cleanup parent buyer + auto-catalog
        await async_cleanup_buyer(async_client, self.BUYER_ID)
