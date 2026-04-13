"""Tests for resource client URL construction, param mapping, response parsing, and pagination."""

from __future__ import annotations

import respx
from httpx import Response

from ordercloud.http import HttpClient
from ordercloud.models import Product, ListPage
from ordercloud.models.order import Order, OrderDirection, OrderStatus
from ordercloud.models.line_item import LineItem
from ordercloud.models.promotion import Promotion
from ordercloud.resources.base import paginate
from ordercloud.resources.products import ProductsResource
from ordercloud.resources.orders import OrdersResource
from ordercloud.resources.line_items import LineItemsResource
from ordercloud.resources.buyers import BuyersResource
from ordercloud.resources.promotions import PromotionsResource
from ordercloud.resources.shipments import ShipmentsResource

from .conftest import TEST_BASE_URL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def list_response(items: list[dict], total: int = 1, page: int = 1) -> dict:
    """Build a mock list response."""
    return {
        "Items": items,
        "Meta": {
            "Page": page,
            "PageSize": 20,
            "TotalCount": total,
            "TotalPages": 1,
            "ItemRange": [1, len(items)],
        },
    }


def facet_list_response(items: list[dict]) -> dict:
    """Build a mock list response with facets."""
    resp = list_response(items, total=len(items))
    resp["Meta"]["Facets"] = [
        {"Name": "Color", "XpPath": "xp.Color", "Values": [{"Value": "Red", "Count": 5}]}
    ]
    return resp


# ---------------------------------------------------------------------------
# ProductsResource
# ---------------------------------------------------------------------------


class TestProductsResource:
    @respx.mock
    async def test_list(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(200, json=facet_list_response([{"ID": "p1", "Name": "Widget"}]))
        )
        resource = ProductsResource(http_client)
        page = await resource.list(search="widget", page_size=20)
        assert isinstance(page, ListPage)
        assert len(page.items) == 1
        assert page.items[0].id == "p1"

    @respx.mock
    async def test_list_passes_search_params(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(200, json=facet_list_response([]))
        )
        resource = ProductsResource(http_client)
        await resource.list(search="test", search_on="Name,Description", sort_by="!DateCreated")
        url = str(route.calls[0].request.url)
        assert "search=test" in url
        assert "searchOn=Name" in url
        assert "sortBy=" in url

    @respx.mock
    async def test_list_passes_filters(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(200, json=facet_list_response([]))
        )
        resource = ProductsResource(http_client)
        await resource.list(filters={"Active": True, "Name": "Widget*"})
        url = str(route.calls[0].request.url)
        assert "Active=" in url
        assert "Name=" in url

    @respx.mock
    async def test_get(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/products/my-prod").mock(
            return_value=Response(200, json={"ID": "my-prod", "Name": "Widget"})
        )
        resource = ProductsResource(http_client)
        product = await resource.get("my-prod")
        assert isinstance(product, Product)
        assert product.id == "my-prod"

    @respx.mock
    async def test_create(self, http_client: HttpClient):
        route = respx.post(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(201, json={"ID": "new-id", "Name": "Widget"})
        )
        resource = ProductsResource(http_client)
        product = await resource.create(Product(Name="Widget", Active=True))
        assert product.id == "new-id"
        body = route.calls[0].request.content.decode()
        assert '"Name"' in body

    @respx.mock
    async def test_create_with_dict(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(201, json={"ID": "d1", "Name": "Dict Product"})
        )
        resource = ProductsResource(http_client)
        product = await resource.create({"Name": "Dict Product", "Active": True})
        assert product.id == "d1"

    @respx.mock
    async def test_save(self, http_client: HttpClient):
        respx.put(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Updated"})
        )
        resource = ProductsResource(http_client)
        product = await resource.save("p1", Product(Name="Updated"))
        assert product.name == "Updated"

    @respx.mock
    async def test_patch(self, http_client: HttpClient):
        respx.patch(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Patched"})
        )
        resource = ProductsResource(http_client)
        product = await resource.patch("p1", {"Name": "Patched"})
        assert product.name == "Patched"

    @respx.mock
    async def test_delete(self, http_client: HttpClient):
        route = respx.delete(f"{TEST_BASE_URL}/products/p1").mock(return_value=Response(204))
        resource = ProductsResource(http_client)
        result = await resource.delete("p1")
        assert result is None
        assert route.called


# ---------------------------------------------------------------------------
# OrdersResource
# ---------------------------------------------------------------------------


class TestOrdersResource:
    @respx.mock
    async def test_list_with_direction(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/orders/Incoming").mock(
            return_value=Response(200, json=list_response([{"ID": "o1", "Status": "Open"}]))
        )
        resource = OrdersResource(http_client)
        page = await resource.list(OrderDirection.Incoming)
        assert len(page.items) == 1

    @respx.mock
    async def test_get(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/orders/Outgoing/ord-1").mock(
            return_value=Response(200, json={"ID": "ord-1", "Status": "Unsubmitted"})
        )
        resource = OrdersResource(http_client)
        order = await resource.get(OrderDirection.Outgoing, "ord-1")
        assert order.status == OrderStatus.Unsubmitted

    @respx.mock
    async def test_create(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/orders/Outgoing").mock(
            return_value=Response(201, json={"ID": "new-ord", "Status": "Unsubmitted"})
        )
        resource = OrdersResource(http_client)
        order = await resource.create(OrderDirection.Outgoing, Order(Comments="Rush"))
        assert order.id == "new-ord"

    @respx.mock
    async def test_submit(self, http_client: HttpClient):
        route = respx.post(f"{TEST_BASE_URL}/orders/Outgoing/o1/submit").mock(
            return_value=Response(200, json={"ID": "o1", "Status": "AwaitingApproval"})
        )
        resource = OrdersResource(http_client)
        order = await resource.submit(OrderDirection.Outgoing, "o1")
        assert order.status == OrderStatus.AwaitingApproval
        assert route.called

    @respx.mock
    async def test_approve(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/orders/Incoming/o1/approve").mock(
            return_value=Response(200, json={"ID": "o1", "Status": "Open"})
        )
        resource = OrdersResource(http_client)
        from ordercloud.models.order import OrderApprovalInfo

        order = await resource.approve(
            OrderDirection.Incoming,
            "o1",
            OrderApprovalInfo(Comments="Approved"),
        )
        assert order.status == OrderStatus.Open

    @respx.mock
    async def test_cancel(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/orders/Incoming/o1/cancel").mock(
            return_value=Response(200, json={"ID": "o1", "Status": "Canceled"})
        )
        resource = OrdersResource(http_client)
        order = await resource.cancel(OrderDirection.Incoming, "o1")
        assert order.status == OrderStatus.Canceled

    @respx.mock
    async def test_delete(self, http_client: HttpClient):
        route = respx.delete(f"{TEST_BASE_URL}/orders/Outgoing/o1").mock(return_value=Response(204))
        resource = OrdersResource(http_client)
        await resource.delete(OrderDirection.Outgoing, "o1")
        assert route.called


# ---------------------------------------------------------------------------
# LineItemsResource
# ---------------------------------------------------------------------------


class TestLineItemsResource:
    @respx.mock
    async def test_list(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/orders/Outgoing/o1/lineitems").mock(
            return_value=Response(
                200, json=list_response([{"ID": "li1", "ProductID": "p1", "Quantity": 2}])
            )
        )
        resource = LineItemsResource(http_client)
        page = await resource.list(OrderDirection.Outgoing, "o1")
        assert len(page.items) == 1
        assert page.items[0].quantity == 2

    @respx.mock
    async def test_create(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/orders/Outgoing/o1/lineitems").mock(
            return_value=Response(201, json={"ID": "li-new", "ProductID": "p1", "Quantity": 3})
        )
        resource = LineItemsResource(http_client)
        li = await resource.create(
            OrderDirection.Outgoing, "o1", LineItem(ProductID="p1", Quantity=3)
        )
        assert li.id == "li-new"

    @respx.mock
    async def test_get(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/orders/Outgoing/o1/lineitems/li1").mock(
            return_value=Response(200, json={"ID": "li1", "ProductID": "p1", "Quantity": 5})
        )
        resource = LineItemsResource(http_client)
        li = await resource.get(OrderDirection.Outgoing, "o1", "li1")
        assert li.quantity == 5


# ---------------------------------------------------------------------------
# Phase 2 resources — spot checks
# ---------------------------------------------------------------------------


class TestPhase2Resources:
    @respx.mock
    async def test_buyers_list(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/buyers").mock(
            return_value=Response(200, json=list_response([{"ID": "b1", "Name": "Acme"}]))
        )
        resource = BuyersResource(http_client)
        page = await resource.list()
        assert page.items[0].name == "Acme"

    @respx.mock
    async def test_promotions_create(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/promotions").mock(
            return_value=Response(201, json={"ID": "promo-1", "Code": "SAVE10"})
        )
        resource = PromotionsResource(http_client)
        promo = await resource.create(Promotion(Code="SAVE10", Name="10% Off"))
        assert promo.code == "SAVE10"

    @respx.mock
    async def test_shipments_get(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/shipments/ship-1").mock(
            return_value=Response(200, json={"ID": "ship-1", "BuyerID": "b1"})
        )
        resource = ShipmentsResource(http_client)
        shipment = await resource.get("ship-1")
        assert shipment.buyer_id == "b1"


# ---------------------------------------------------------------------------
# Auto-pagination
# ---------------------------------------------------------------------------


def paged_response(items: list[dict], page: int, total_pages: int, total_count: int) -> dict:
    """Build a mock paginated response."""
    return {
        "Items": items,
        "Meta": {
            "Page": page,
            "PageSize": 2,
            "TotalCount": total_count,
            "TotalPages": total_pages,
            "ItemRange": [1, len(items)],
            "Facets": [],
        },
    }


class TestPagination:
    @respx.mock
    async def test_single_page(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/buyers").mock(
            return_value=Response(
                200,
                json=paged_response(
                    [{"ID": "b1", "Name": "One"}, {"ID": "b2", "Name": "Two"}],
                    page=1,
                    total_pages=1,
                    total_count=2,
                ),
            )
        )
        resource = BuyersResource(http_client)
        items = [item async for item in paginate(resource.list, page_size=2)]
        assert len(items) == 2
        assert items[0].id == "b1"
        assert items[1].id == "b2"

    @respx.mock
    async def test_multiple_pages(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/buyers").mock(
            side_effect=[
                Response(
                    200,
                    json=paged_response(
                        [{"ID": "b1"}, {"ID": "b2"}],
                        page=1,
                        total_pages=3,
                        total_count=5,
                    ),
                ),
                Response(
                    200,
                    json=paged_response(
                        [{"ID": "b3"}, {"ID": "b4"}],
                        page=2,
                        total_pages=3,
                        total_count=5,
                    ),
                ),
                Response(
                    200,
                    json=paged_response(
                        [{"ID": "b5"}],
                        page=3,
                        total_pages=3,
                        total_count=5,
                    ),
                ),
            ]
        )
        resource = BuyersResource(http_client)
        items = [item async for item in paginate(resource.list, page_size=2)]
        assert len(items) == 5
        assert [b.id for b in items] == ["b1", "b2", "b3", "b4", "b5"]
        assert route.call_count == 3

    @respx.mock
    async def test_empty_result(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/buyers").mock(
            return_value=Response(
                200,
                json=paged_response([], page=1, total_pages=0, total_count=0),
            )
        )
        resource = BuyersResource(http_client)
        items = [item async for item in paginate(resource.list)]
        assert items == []

    @respx.mock
    async def test_passes_kwargs(self, http_client: HttpClient):
        route = respx.get(f"{TEST_BASE_URL}/buyers").mock(
            return_value=Response(
                200,
                json=paged_response([{"ID": "b1"}], page=1, total_pages=1, total_count=1),
            )
        )
        resource = BuyersResource(http_client)
        items = [item async for item in paginate(resource.list, search="acme")]
        assert len(items) == 1
        url = str(route.calls[0].request.url)
        assert "search=acme" in url

    @respx.mock
    async def test_with_positional_args(self, http_client: HttpClient):
        """paginate works with list methods that take positional args (e.g. orders)."""
        respx.get(f"{TEST_BASE_URL}/orders/Incoming").mock(
            return_value=Response(
                200,
                json=paged_response(
                    [{"ID": "o1", "Status": "Open"}],
                    page=1,
                    total_pages=1,
                    total_count=1,
                ),
            )
        )
        resource = OrdersResource(http_client)
        items = [item async for item in paginate(resource.list, OrderDirection.Incoming)]
        assert len(items) == 1
        assert items[0].id == "o1"


# ---------------------------------------------------------------------------
# Async client — create() factory and context manager
# ---------------------------------------------------------------------------


class TestAsyncClientLifecycle:
    @respx.mock
    async def test_create_factory(self):
        from ordercloud import OrderCloudClient
        from ordercloud.auth import AccessToken

        respx.get(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Widget"})
        )

        client = OrderCloudClient.create(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url=TEST_BASE_URL,
            auth_url="https://test-auth.ordercloud.io/oauth/token",
        )
        client._token_manager._token = AccessToken("mock-token-12345", expires_in=600)

        product = await client.products.get("p1")
        assert product.id == "p1"
        await client.close()

    @respx.mock
    async def test_async_context_manager(self):
        from ordercloud import OrderCloudClient
        from ordercloud.auth import AccessToken

        respx.get(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Widget"})
        )

        client = OrderCloudClient.create(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url=TEST_BASE_URL,
            auth_url="https://test-auth.ordercloud.io/oauth/token",
        )
        client._token_manager._token = AccessToken("mock-token-12345", expires_in=600)

        async with client as c:
            product = await c.products.get("p1")
            assert product.id == "p1"

    @respx.mock
    async def test_list_with_depth_param(self, http_client: HttpClient):
        """Exercise the depth parameter branch in _build_list_params."""
        from ordercloud.resources.categories import CategoriesResource

        route = respx.get(f"{TEST_BASE_URL}/catalogs/cat1/categories").mock(
            return_value=Response(
                200,
                json=list_response([{"ID": "c1", "Name": "Root"}]),
            )
        )
        resource = CategoriesResource(http_client)
        page = await resource.list("cat1", depth="all")
        assert len(page.items) == 1
        url = str(route.calls[0].request.url)
        assert "depth=all" in url
