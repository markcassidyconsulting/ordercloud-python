"""Tests for resource client URL construction, param mapping, and response parsing."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ordercloud.http import HttpClient
from ordercloud.models import Product, ListPage, MetaWithFacets
from ordercloud.models.order import Order, OrderDirection, OrderStatus
from ordercloud.models.line_item import LineItem
from ordercloud.models.buyer import Buyer
from ordercloud.models.promotion import Promotion
from ordercloud.models.shipment import Shipment
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
        assert len(page.Items) == 1
        assert page.Items[0].ID == "p1"

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
        assert product.ID == "my-prod"

    @respx.mock
    async def test_create(self, http_client: HttpClient):
        route = respx.post(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(201, json={"ID": "new-id", "Name": "Widget"})
        )
        resource = ProductsResource(http_client)
        product = await resource.create(Product(Name="Widget", Active=True))
        assert product.ID == "new-id"
        body = route.calls[0].request.content.decode()
        assert '"Name"' in body

    @respx.mock
    async def test_create_with_dict(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/products").mock(
            return_value=Response(201, json={"ID": "d1", "Name": "Dict Product"})
        )
        resource = ProductsResource(http_client)
        product = await resource.create({"Name": "Dict Product", "Active": True})
        assert product.ID == "d1"

    @respx.mock
    async def test_save(self, http_client: HttpClient):
        respx.put(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Updated"})
        )
        resource = ProductsResource(http_client)
        product = await resource.save("p1", Product(Name="Updated"))
        assert product.Name == "Updated"

    @respx.mock
    async def test_patch(self, http_client: HttpClient):
        route = respx.patch(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(200, json={"ID": "p1", "Name": "Patched"})
        )
        resource = ProductsResource(http_client)
        product = await resource.patch("p1", {"Name": "Patched"})
        assert product.Name == "Patched"

    @respx.mock
    async def test_delete(self, http_client: HttpClient):
        route = respx.delete(f"{TEST_BASE_URL}/products/p1").mock(
            return_value=Response(204)
        )
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
        assert len(page.Items) == 1

    @respx.mock
    async def test_get(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/orders/Outgoing/ord-1").mock(
            return_value=Response(200, json={"ID": "ord-1", "Status": "Unsubmitted"})
        )
        resource = OrdersResource(http_client)
        order = await resource.get(OrderDirection.Outgoing, "ord-1")
        assert order.Status == OrderStatus.Unsubmitted

    @respx.mock
    async def test_create(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/orders/Outgoing").mock(
            return_value=Response(201, json={"ID": "new-ord", "Status": "Unsubmitted"})
        )
        resource = OrdersResource(http_client)
        order = await resource.create(OrderDirection.Outgoing, Order(Comments="Rush"))
        assert order.ID == "new-ord"

    @respx.mock
    async def test_submit(self, http_client: HttpClient):
        route = respx.post(f"{TEST_BASE_URL}/orders/Outgoing/o1/submit").mock(
            return_value=Response(200, json={"ID": "o1", "Status": "AwaitingApproval"})
        )
        resource = OrdersResource(http_client)
        order = await resource.submit(OrderDirection.Outgoing, "o1")
        assert order.Status == OrderStatus.AwaitingApproval
        assert route.called

    @respx.mock
    async def test_approve(self, http_client: HttpClient):
        route = respx.post(f"{TEST_BASE_URL}/orders/Incoming/o1/approve").mock(
            return_value=Response(200, json={"ID": "o1", "Status": "Open"})
        )
        resource = OrdersResource(http_client)
        from ordercloud.models.order import OrderApprovalInfo
        order = await resource.approve(
            OrderDirection.Incoming, "o1",
            OrderApprovalInfo(Comments="Approved"),
        )
        assert order.Status == OrderStatus.Open

    @respx.mock
    async def test_cancel(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/orders/Incoming/o1/cancel").mock(
            return_value=Response(200, json={"ID": "o1", "Status": "Canceled"})
        )
        resource = OrdersResource(http_client)
        order = await resource.cancel(OrderDirection.Incoming, "o1")
        assert order.Status == OrderStatus.Canceled

    @respx.mock
    async def test_delete(self, http_client: HttpClient):
        route = respx.delete(f"{TEST_BASE_URL}/orders/Outgoing/o1").mock(
            return_value=Response(204)
        )
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
        assert len(page.Items) == 1
        assert page.Items[0].Quantity == 2

    @respx.mock
    async def test_create(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/orders/Outgoing/o1/lineitems").mock(
            return_value=Response(201, json={"ID": "li-new", "ProductID": "p1", "Quantity": 3})
        )
        resource = LineItemsResource(http_client)
        li = await resource.create(
            OrderDirection.Outgoing, "o1", LineItem(ProductID="p1", Quantity=3)
        )
        assert li.ID == "li-new"

    @respx.mock
    async def test_get(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/orders/Outgoing/o1/lineitems/li1").mock(
            return_value=Response(200, json={"ID": "li1", "ProductID": "p1", "Quantity": 5})
        )
        resource = LineItemsResource(http_client)
        li = await resource.get(OrderDirection.Outgoing, "o1", "li1")
        assert li.Quantity == 5


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
        assert page.Items[0].Name == "Acme"

    @respx.mock
    async def test_promotions_create(self, http_client: HttpClient):
        respx.post(f"{TEST_BASE_URL}/promotions").mock(
            return_value=Response(201, json={"ID": "promo-1", "Code": "SAVE10"})
        )
        resource = PromotionsResource(http_client)
        promo = await resource.create(Promotion(Code="SAVE10", Name="10% Off"))
        assert promo.Code == "SAVE10"

    @respx.mock
    async def test_shipments_get(self, http_client: HttpClient):
        respx.get(f"{TEST_BASE_URL}/shipments/ship-1").mock(
            return_value=Response(200, json={"ID": "ship-1", "BuyerID": "b1"})
        )
        resource = ShipmentsResource(http_client)
        shipment = await resource.get("ship-1")
        assert shipment.BuyerID == "b1"
