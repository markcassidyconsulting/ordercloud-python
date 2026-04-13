"""Integration tests: synchronous client wrapper.

Verifies that SyncOrderCloudClient and paginate_sync work end-to-end
against the live sandbox.
"""

from __future__ import annotations

import pytest

from ordercloud import OrderCloudError, SyncOrderCloudClient, paginate_sync

from .conftest import safe_delete, wait_for_listed_sync


class TestSyncClient:
    """Verify SyncOrderCloudClient works end-to-end."""

    PID = "inttest-sync-product"

    def test_sync_crud(self, sync_client: SyncOrderCloudClient) -> None:
        """Basic CRUD lifecycle using the sync client."""
        # Pre-cleanup
        safe_delete(sync_client.products.delete, self.PID)

        # Create
        product = sync_client.products.save(
            self.PID, {"ID": self.PID, "Name": "Sync Test Product", "Active": True}
        )
        assert product.id == self.PID
        assert product.name == "Sync Test Product"

        # Get
        fetched = sync_client.products.get(self.PID)
        assert fetched.id == self.PID

        # Patch
        updated = sync_client.products.patch(self.PID, {"Name": "Sync Updated"})
        assert updated.name == "Sync Updated"

        # List with filter (retry-based wait for search index)
        page = wait_for_listed_sync(sync_client.products.list, self.PID, filters={"ID": self.PID})
        assert any(p.id == self.PID for p in page.items)

        # Delete
        sync_client.products.delete(self.PID)

    def test_paginate_sync(self, sync_client: SyncOrderCloudClient) -> None:
        """paginate_sync yields items across pages."""
        pids = [f"inttest-sync-page-{i}" for i in range(3)]

        # Pre-cleanup
        for pid in pids:
            safe_delete(sync_client.products.delete, pid)

        for pid in pids:
            sync_client.products.save(pid, {"ID": pid, "Name": f"Sync Page {pid}", "Active": True})

        try:
            # Wait for first product to appear in search index
            wait_for_listed_sync(
                sync_client.products.list, pids[0], filters={"ID": "inttest-sync-page-*"}
            )

            items = list(
                paginate_sync(
                    sync_client.products.list,
                    page_size=2,
                    filters={"ID": "inttest-sync-page-*"},
                )
            )
            returned_ids = {p.id for p in items}
            for pid in pids:
                assert pid in returned_ids, f"Missing {pid} from paginate_sync results"

        finally:
            for pid in pids:
                safe_delete(sync_client.products.delete, pid)

    def test_sync_error_handling(self, sync_client: SyncOrderCloudClient) -> None:
        """Errors are raised correctly through the sync wrapper."""
        with pytest.raises(OrderCloudError) as exc_info:
            sync_client.products.get("nonexistent-sync-product-xyz")
        assert exc_info.value.status_code == 404
