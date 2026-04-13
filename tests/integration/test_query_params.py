"""Integration tests: query parameter passing on non-GET methods.

Validates the delete_assignment fix — query parameters must be sent on
DELETE requests, not silently discarded.  Also exercises POST-with-body
assignment endpoints.
"""

from __future__ import annotations

from ordercloud import OrderCloudClient

from .conftest import async_cleanup_buyer, async_safe_delete


class TestCatalogAssignments:
    """Catalog <-> buyer assignment lifecycle with query-param DELETE."""

    BUYER_ID = "inttest-assign-buyer"
    CATALOG_ID = "inttest-assign-catalog"

    async def test_catalog_assignment_lifecycle(self, async_client: OrderCloudClient) -> None:
        """save_assignment -> list -> delete_assignment (DELETE + query params) -> verify gone."""
        # Pre-cleanup: buyer + auto-catalog from previous runs
        await async_cleanup_buyer(async_client, self.BUYER_ID)
        await async_safe_delete(async_client.catalogs.delete(self.CATALOG_ID))

        # Setup: buyer + catalog
        await async_client.buyers.save(
            self.BUYER_ID, {"ID": self.BUYER_ID, "Name": "Assignment Test Buyer", "Active": True}
        )
        await async_client.catalogs.save(
            self.CATALOG_ID,
            {"ID": self.CATALOG_ID, "Name": "Assignment Test Catalog", "Active": True},
        )

        try:
            # --- Save assignment (POST with JSON body) ---
            await async_client.catalogs.save_assignment(
                {"CatalogID": self.CATALOG_ID, "BuyerID": self.BUYER_ID}
            )

            # --- List assignments (GET with query params) ---
            page = await async_client.catalogs.list_assignments(
                catalog_id=self.CATALOG_ID, buyer_id=self.BUYER_ID
            )
            assert page.Meta.TotalCount >= 1
            assert any(
                a.CatalogID == self.CATALOG_ID and a.BuyerID == self.BUYER_ID for a in page.Items
            )

            # --- Delete assignment (DELETE with query params) ---
            # This is the critical test: buyer_id is sent as a query parameter
            # on the DELETE request.  Before the fix, this param was silently
            # discarded and the delete would fail or remove the wrong thing.
            await async_client.catalogs.delete_assignment(self.CATALOG_ID, buyer_id=self.BUYER_ID)

            # --- Verify the assignment is gone ---
            page = await async_client.catalogs.list_assignments(
                catalog_id=self.CATALOG_ID, buyer_id=self.BUYER_ID
            )
            matching = [
                a
                for a in page.Items
                if a.CatalogID == self.CATALOG_ID and a.BuyerID == self.BUYER_ID
            ]
            assert len(matching) == 0, "Assignment should be deleted"

        finally:
            await async_safe_delete(
                async_client.catalogs.delete_assignment(self.CATALOG_ID, buyer_id=self.BUYER_ID)
            )
            await async_safe_delete(async_client.catalogs.delete(self.CATALOG_ID))
            await async_cleanup_buyer(async_client, self.BUYER_ID)


class TestCategoryAssignments:
    """Category assignment with query-param-bearing DELETE."""

    BUYER_ID = "inttest-catassign-buyer"
    CATALOG_ID = "inttest-catassign-catalog"
    CATEGORY_ID = "inttest-catassign-cat"

    async def test_category_assignment_lifecycle(self, async_client: OrderCloudClient) -> None:
        """Full chain: catalog -> buyer -> category -> assignment -> delete."""
        # Pre-cleanup
        await async_cleanup_buyer(async_client, self.BUYER_ID)
        await async_safe_delete(async_client.catalogs.delete(self.CATALOG_ID))

        # Setup infrastructure
        await async_client.buyers.save(
            self.BUYER_ID, {"ID": self.BUYER_ID, "Name": "CatAssign Buyer", "Active": True}
        )
        await async_client.catalogs.save(
            self.CATALOG_ID,
            {"ID": self.CATALOG_ID, "Name": "CatAssign Catalog", "Active": True},
        )
        # Catalog must be assigned to buyer before category assignments work
        await async_client.catalogs.save_assignment(
            {"CatalogID": self.CATALOG_ID, "BuyerID": self.BUYER_ID}
        )
        await async_client.categories.save(
            self.CATALOG_ID,
            self.CATEGORY_ID,
            {"ID": self.CATEGORY_ID, "Name": "CatAssign Category", "Active": True},
        )

        try:
            # --- Save category assignment ---
            await async_client.categories.save_assignment(
                self.CATALOG_ID,
                {"CategoryID": self.CATEGORY_ID, "BuyerID": self.BUYER_ID},
            )

            # --- List ---
            page = await async_client.categories.list_assignments(
                self.CATALOG_ID, buyer_id=self.BUYER_ID
            )
            assert page.Meta.TotalCount >= 1

            # --- Delete (buyer_id as query param on DELETE) ---
            await async_client.categories.delete_assignment(
                self.CATALOG_ID,
                self.CATEGORY_ID,
                buyer_id=self.BUYER_ID,
            )

            # --- Verify gone ---
            page = await async_client.categories.list_assignments(
                self.CATALOG_ID,
                category_id=self.CATEGORY_ID,
                buyer_id=self.BUYER_ID,
            )
            assert page.Meta.TotalCount == 0

        finally:
            await async_safe_delete(
                async_client.categories.delete_assignment(
                    self.CATALOG_ID, self.CATEGORY_ID, buyer_id=self.BUYER_ID
                )
            )
            await async_safe_delete(
                async_client.catalogs.delete_assignment(self.CATALOG_ID, buyer_id=self.BUYER_ID)
            )
            await async_safe_delete(
                async_client.categories.delete(self.CATALOG_ID, self.CATEGORY_ID)
            )
            await async_safe_delete(async_client.catalogs.delete(self.CATALOG_ID))
            await async_cleanup_buyer(async_client, self.BUYER_ID)


class TestProductCatalogAssignments:
    """Product -> catalog assignment (POST with body, no query params on delete)."""

    CATALOG_ID = "inttest-prodcat-catalog"
    PRODUCT_ID = "inttest-prodcat-product"

    async def test_product_catalog_assignment(self, async_client: OrderCloudClient) -> None:
        """Assign a product to a catalog, list, remove, verify."""
        await async_client.catalogs.save(
            self.CATALOG_ID,
            {"ID": self.CATALOG_ID, "Name": "ProdCat Catalog", "Active": True},
        )
        await async_client.products.save(
            self.PRODUCT_ID,
            {"ID": self.PRODUCT_ID, "Name": "ProdCat Product", "Active": True},
        )

        try:
            # Assign product to catalog
            await async_client.catalogs.save_product_assignment(
                {"CatalogID": self.CATALOG_ID, "ProductID": self.PRODUCT_ID}
            )

            # List product-catalog assignments
            page = await async_client.catalogs.list_product_assignments(
                catalog_id=self.CATALOG_ID, product_id=self.PRODUCT_ID
            )
            assert page.Meta.TotalCount >= 1

            # Remove
            await async_client.catalogs.delete_product_assignment(self.CATALOG_ID, self.PRODUCT_ID)

            # Verify gone
            page = await async_client.catalogs.list_product_assignments(
                catalog_id=self.CATALOG_ID, product_id=self.PRODUCT_ID
            )
            assert page.Meta.TotalCount == 0

        finally:
            await async_safe_delete(
                async_client.catalogs.delete_product_assignment(self.CATALOG_ID, self.PRODUCT_ID)
            )
            await async_safe_delete(async_client.products.delete(self.PRODUCT_ID))
            await async_safe_delete(async_client.catalogs.delete(self.CATALOG_ID))
