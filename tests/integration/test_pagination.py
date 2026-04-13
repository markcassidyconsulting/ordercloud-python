"""Integration tests: auto-pagination across real list endpoints.

Creates multiple products and verifies that ``paginate()`` yields all
items when the page size is smaller than the total count.
"""

from __future__ import annotations

from ordercloud import OrderCloudClient, paginate

from .conftest import async_safe_delete, wait_for_listed

PRODUCT_IDS = [f"inttest-page-{i}" for i in range(5)]


class TestPagination:
    """Verify auto-pagination helpers against real endpoints."""

    async def test_auto_pagination_yields_all_items(self, async_client: OrderCloudClient) -> None:
        """paginate() yields every item across multiple pages."""
        # Pre-cleanup
        for pid in PRODUCT_IDS:
            await async_safe_delete(async_client.products.delete(pid))

        # Create 5 products
        for pid in PRODUCT_IDS:
            await async_client.products.save(
                pid, {"ID": pid, "Name": f"Page Test {pid}", "Active": True}
            )

        try:
            # Wait for search index, then paginate with page_size=2
            await wait_for_listed(
                async_client.products.list, PRODUCT_IDS[0], filters={"ID": "inttest-page-*"}
            )
            items = []
            async for product in paginate(
                async_client.products.list,
                page_size=2,
                filters={"ID": "inttest-page-*"},
            ):
                items.append(product)

            returned_ids = {p.id for p in items}
            for pid in PRODUCT_IDS:
                assert pid in returned_ids, f"Missing {pid} from paginated results"

            assert len(items) >= len(PRODUCT_IDS)

        finally:
            for pid in PRODUCT_IDS:
                await async_safe_delete(async_client.products.delete(pid))

    async def test_list_metadata_populated(self, async_client: OrderCloudClient) -> None:
        """List response Meta fields are populated correctly."""
        page = await async_client.products.list(page=1, page_size=5)

        assert page.meta.page == 1
        assert page.meta.page_size == 5
        assert isinstance(page.meta.total_count, int)
        assert isinstance(page.meta.total_pages, int)
        assert page.meta.total_count >= 0
        assert page.meta.total_pages >= 0

    async def test_search_and_sort(self, async_client: OrderCloudClient) -> None:
        """Search and sort_by query parameters work against the live API."""
        pid = "inttest-search-test"
        await async_safe_delete(async_client.products.delete(pid))
        await async_client.products.save(
            pid, {"ID": pid, "Name": "Searchable Widget Foo", "Active": True}
        )
        try:
            # Wait for search index
            await wait_for_listed(
                async_client.products.list,
                pid,
                search="Searchable Widget Foo",
                search_on="Name",
                sort_by="Name",
                page_size=10,
            )

            page = await async_client.products.list(
                search="Searchable Widget Foo",
                search_on="Name",
                sort_by="Name",
                page_size=10,
            )
            assert any(p.id == pid for p in page.items)
        finally:
            await async_safe_delete(async_client.products.delete(pid))
