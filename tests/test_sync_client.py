"""Tests for the synchronous client wrapper."""

from __future__ import annotations

import respx
from httpx import Response

from ordercloud.auth import AccessToken
from ordercloud.config import OrderCloudConfig
from ordercloud.models.product import Product
from ordercloud.models.shared import ListPage
from ordercloud.sync_client import SyncOrderCloudClient, paginate_sync

from .conftest import TEST_BASE_URL, TEST_AUTH_URL, TEST_CLIENT_ID, TEST_CLIENT_SECRET


def _make_sync_client() -> SyncOrderCloudClient:
    """Create a sync client with a pre-populated mock token."""
    config = OrderCloudConfig(
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
        base_url=TEST_BASE_URL,
        auth_url=TEST_AUTH_URL,
        scopes=["FullAccess"],
        timeout=5.0,
    )
    client = SyncOrderCloudClient(config)
    # Pre-populate token to avoid auth calls in tests.
    client._async_client._token_manager._token = AccessToken(
        "mock-token-12345", expires_in=600
    )
    return client


class TestSyncClient:
    @respx.mock
    def test_list_products(self):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                200,
                json={
                    "Items": [{"ID": "p1", "Name": "Widget"}],
                    "Meta": {
                        "Page": 1,
                        "PageSize": 20,
                        "TotalCount": 1,
                        "TotalPages": 1,
                        "ItemRange": [1, 1],
                        "Facets": [],
                    },
                },
            )
        )
        client = _make_sync_client()
        try:
            page = client.products.list()
            assert isinstance(page, ListPage)
            assert len(page.Items) == 1
            assert page.Items[0].ID == "p1"
        finally:
            client.close()

    @respx.mock
    def test_get_product(self):
        respx.get(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Widget"})
        )
        client = _make_sync_client()
        try:
            product = client.products.get("p1")
            assert isinstance(product, Product)
            assert product.Name == "Widget"
        finally:
            client.close()

    @respx.mock
    def test_create_product(self):
        respx.post(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(201, json={"ID": "new", "Name": "Widget"})
        )
        client = _make_sync_client()
        try:
            product = client.products.create({"Name": "Widget"})
            assert product.ID == "new"
        finally:
            client.close()

    @respx.mock
    def test_delete_product(self):
        route = respx.delete(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(204)
        )
        client = _make_sync_client()
        try:
            result = client.products.delete("p1")
            assert result is None
            assert route.called
        finally:
            client.close()

    @respx.mock
    def test_context_manager(self):
        respx.get(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Widget"})
        )
        with _make_sync_client() as client:
            product = client.products.get("p1")
            assert product.ID == "p1"

    @respx.mock
    def test_create_factory(self):
        respx.get(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Widget"})
        )
        client = SyncOrderCloudClient.create(
            client_id=TEST_CLIENT_ID,
            client_secret=TEST_CLIENT_SECRET,
            base_url=TEST_BASE_URL,
            auth_url=TEST_AUTH_URL,
        )
        client._async_client._token_manager._token = AccessToken(
            "mock-token-12345", expires_in=600
        )
        try:
            product = client.products.get("p1")
            assert product.ID == "p1"
        finally:
            client.close()

    def test_has_all_resource_attributes(self):
        client = _make_sync_client()
        try:
            # Spot-check key resource attributes exist
            assert hasattr(client, "products")
            assert hasattr(client, "orders")
            assert hasattr(client, "buyers")
            assert hasattr(client, "catalogs")
            assert hasattr(client, "users")
        finally:
            client.close()

    def test_proxy_non_coroutine_fallback(self):
        """_SyncProxy passes through non-async attributes unchanged."""
        client = _make_sync_client()
        try:
            # _build_list_params is a staticmethod, not a coroutine
            params = client.products._build_list_params(search="test", page=1)
            assert params == {"search": "test", "page": 1}
        finally:
            client.close()

    @respx.mock
    def test_sync_add_before_request(self):
        from ordercloud.middleware import RequestContext

        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                200,
                json={
                    "Items": [],
                    "Meta": {
                        "Page": 1, "PageSize": 20, "TotalCount": 0,
                        "TotalPages": 0, "ItemRange": [], "Facets": [],
                    },
                },
            )
        )

        async def add_header(ctx: RequestContext) -> None:
            ctx.headers["X-Sync-Test"] = "yes"

        with _make_sync_client() as client:
            client.add_before_request(add_header)
            client.products.list()

        assert route.calls[0].request.headers["x-sync-test"] == "yes"

    @respx.mock
    def test_sync_add_after_response(self):
        from ordercloud.middleware import ResponseContext

        respx.get(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Widget"})
        )

        captured: list[ResponseContext] = []

        async def capture(ctx: ResponseContext) -> None:
            captured.append(ctx)

        with _make_sync_client() as client:
            client.add_after_response(capture)
            client.products.get("p1")

        assert len(captured) == 1
        assert captured[0].response.status_code == 200


class TestPaginateSync:
    @respx.mock
    def test_single_page(self):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(
                200,
                json={
                    "Items": [{"ID": "p1"}, {"ID": "p2"}],
                    "Meta": {
                        "Page": 1,
                        "PageSize": 2,
                        "TotalCount": 2,
                        "TotalPages": 1,
                        "ItemRange": [1, 2],
                        "Facets": [],
                    },
                },
            )
        )
        with _make_sync_client() as client:
            items = list(paginate_sync(client.products.list, page_size=2))
            assert len(items) == 2

    @respx.mock
    def test_multiple_pages(self):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "Items": [{"ID": "p1"}, {"ID": "p2"}],
                        "Meta": {
                            "Page": 1,
                            "PageSize": 2,
                            "TotalCount": 3,
                            "TotalPages": 2,
                            "ItemRange": [1, 2],
                            "Facets": [],
                        },
                    },
                ),
                Response(
                    200,
                    json={
                        "Items": [{"ID": "p3"}],
                        "Meta": {
                            "Page": 2,
                            "PageSize": 2,
                            "TotalCount": 3,
                            "TotalPages": 2,
                            "ItemRange": [3, 3],
                            "Facets": [],
                        },
                    },
                ),
            ]
        )
        with _make_sync_client() as client:
            items = list(paginate_sync(client.products.list, page_size=2))
            assert len(items) == 3
            assert [p.ID for p in items] == ["p1", "p2", "p3"]
            assert route.call_count == 2
