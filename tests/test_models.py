"""Tests for Pydantic model serialisation and behaviour."""

from __future__ import annotations

import pytest

from ordercloud.models import (
    Address,
    Buyer,
    Catalog,
    Category,
    ListPage,
    Meta,
    MetaWithFacets,
    OrderCloudModel,
    Product,
)
from ordercloud.models.order import Order, OrderDirection, OrderStatus
from ordercloud.models.line_item import LineItem
from ordercloud.models.line_item_types import LineItemProduct
from ordercloud.models.payment import Payment, PaymentType
from ordercloud.models.price_schedule import PriceSchedule, PriceBreak
from ordercloud.models.shipment import Shipment
from ordercloud.models.promotion import Promotion
from ordercloud.models.security import SecurityProfile


# ---------------------------------------------------------------------------
# Base model behaviour
# ---------------------------------------------------------------------------


class TestOrderCloudModel:
    def test_extra_fields_preserved(self):
        """Unknown fields from the API should not be dropped."""
        p = Product.model_validate({"ID": "x", "UnknownField": "surprise"})
        dumped = p.model_dump()
        assert dumped["UnknownField"] == "surprise"

    def test_populate_by_name(self):
        """Fields can be set by name (PascalCase)."""
        p = Product(ID="x", Name="Widget")
        assert p.ID == "x"
        assert p.Name == "Widget"

    def test_exclude_none(self):
        """model_dump(exclude_none=True) drops None fields."""
        p = Product(ID="x")
        dumped = p.model_dump(exclude_none=True)
        assert "ID" in dumped
        assert "Name" not in dumped
        assert "Description" not in dumped


# ---------------------------------------------------------------------------
# Phase 1 models — round-trip serialisation
# ---------------------------------------------------------------------------


class TestProductModel:
    def test_round_trip(self):
        data = {
            "ID": "prod-1",
            "Name": "Widget",
            "QuantityMultiplier": 5,
            "Active": True,
            "SpecCount": 3,
            "VariantCount": 12,
            "DateCreated": "2026-01-15T10:30:00Z",
            "xp": {"color": "red", "weight": 1.5},
        }
        p = Product.model_validate(data)
        assert p.ID == "prod-1"
        assert p.QuantityMultiplier == 5
        assert p.SpecCount == 3
        assert p.xp == {"color": "red", "weight": 1.5}

        dumped = p.model_dump(exclude_none=True)
        assert dumped["QuantityMultiplier"] == 5
        assert dumped["xp"]["color"] == "red"

    def test_defaults(self):
        p = Product()
        assert p.QuantityMultiplier == 1
        assert p.SpecCount == 0
        assert p.VariantCount == 0
        assert p.xp is None

    def test_inventory_embedded(self):
        data = {
            "ID": "p1",
            "Inventory": {"Enabled": True, "QuantityAvailable": 50},
        }
        p = Product.model_validate(data)
        assert p.Inventory is not None
        assert p.Inventory.Enabled is True


class TestOrderModel:
    def test_round_trip(self):
        data = {
            "ID": "ord-1",
            "Status": "Unsubmitted",
            "LineItemCount": 3,
            "Subtotal": 99.99,
            "Total": 109.99,
            "ShippingCost": 10.0,
            "IsSubmitted": False,
            "xp": {"priority": "high"},
        }
        o = Order.model_validate(data)
        assert o.Status == OrderStatus.Unsubmitted
        assert o.LineItemCount == 3
        assert o.Subtotal == 99.99

    def test_enum_serialises_as_string(self):
        o = Order(Status=OrderStatus.Open)
        dumped = o.model_dump(exclude_none=True)
        assert dumped["Status"] == "Open"

    def test_embedded_user(self):
        data = {
            "ID": "ord-1",
            "FromUser": {"ID": "user-1", "Username": "buyer@test.com"},
        }
        o = Order.model_validate(data)
        assert o.FromUser is not None
        assert o.FromUser.Username == "buyer@test.com"

    def test_embedded_address(self):
        data = {
            "ID": "ord-1",
            "BillingAddress": {
                "Street1": "123 Main St",
                "City": "Portland",
                "Country": "US",
            },
        }
        o = Order.model_validate(data)
        assert o.BillingAddress.City == "Portland"


class TestLineItemModel:
    def test_round_trip(self):
        data = {
            "ID": "li-1",
            "ProductID": "prod-1",
            "Quantity": 3,
            "xp": {"gift_wrap": True},
        }
        li = LineItem.model_validate(data)
        assert li.ProductID == "prod-1"
        assert li.Quantity == 3

    def test_defaults(self):
        li = LineItem()
        assert li.Quantity == 1


class TestAddressModel:
    def test_round_trip(self):
        data = {
            "ID": "addr-1",
            "Street1": "123 Main St",
            "City": "Portland",
            "State": "OR",
            "Zip": "97201",
            "Country": "US",
        }
        a = Address.model_validate(data)
        dumped = a.model_dump(exclude_none=True)
        assert dumped["Street1"] == "123 Main St"
        assert dumped["Country"] == "US"


class TestBuyerModel:
    def test_round_trip(self):
        data = {"ID": "buyer-1", "Name": "Acme Corp", "Active": True}
        b = Buyer.model_validate(data)
        assert b.Name == "Acme Corp"


class TestCatalogModel:
    def test_round_trip(self):
        data = {"ID": "cat-1", "Name": "Spring 2026", "Active": True}
        c = Catalog.model_validate(data)
        assert c.Name == "Spring 2026"


class TestCategoryModel:
    def test_round_trip(self):
        data = {"ID": "category-1", "Name": "Electronics", "Active": True}
        c = Category.model_validate(data)
        assert c.Name == "Electronics"


# ---------------------------------------------------------------------------
# Phase 2 model sampling
# ---------------------------------------------------------------------------


class TestPhase2Models:
    def test_payment_with_enum(self):
        data = {"ID": "pay-1", "Type": "CreditCard", "Amount": 99.99}
        p = Payment.model_validate(data)
        assert p.Type == PaymentType.CreditCard
        dumped = p.model_dump(exclude_none=True)
        assert dumped["Type"] == "CreditCard"

    def test_price_schedule_with_breaks(self):
        data = {
            "ID": "ps-1",
            "Name": "Bulk Pricing",
            "PriceBreaks": [
                {"Quantity": 1, "Price": 10.0},
                {"Quantity": 10, "Price": 8.0},
            ],
        }
        ps = PriceSchedule.model_validate(data)
        assert len(ps.PriceBreaks) == 2
        assert ps.PriceBreaks[1].Price == 8.0

    def test_promotion(self):
        data = {
            "ID": "promo-1",
            "Code": "SAVE10",
            "Name": "10% Off",
            "Active": True,
        }
        p = Promotion.model_validate(data)
        assert p.Code == "SAVE10"

    def test_shipment(self):
        data = {
            "ID": "ship-1",
            "BuyerID": "buyer-1",
            "DateShipped": "2026-04-13T12:00:00Z",
        }
        s = Shipment.model_validate(data)
        assert s.BuyerID == "buyer-1"

    def test_security_profile(self):
        data = {"ID": "sp-1", "Name": "Buyer Admin", "Roles": ["BuyerAdmin", "AddressAdmin"]}
        sp = SecurityProfile.model_validate(data)
        assert "BuyerAdmin" in sp.Roles


# ---------------------------------------------------------------------------
# Enum serialisation
# ---------------------------------------------------------------------------


class TestEnums:
    def test_order_direction_values(self):
        assert OrderDirection.Incoming.value == "Incoming"
        assert OrderDirection.Outgoing.value == "Outgoing"
        assert OrderDirection.All.value == "All"

    def test_order_status_values(self):
        assert OrderStatus.Unsubmitted.value == "Unsubmitted"
        assert OrderStatus.AwaitingApproval.value == "AwaitingApproval"
        assert OrderStatus.Canceled.value == "Canceled"

    def test_enum_is_str(self):
        """Enums are str subclasses — usable directly in f-strings."""
        d = OrderDirection.Incoming
        assert f"/orders/{d}" == "/orders/Incoming"

    def test_payment_type_values(self):
        assert PaymentType.CreditCard.value == "CreditCard"
        assert PaymentType.PurchaseOrder.value == "PurchaseOrder"


# ---------------------------------------------------------------------------
# Pagination types
# ---------------------------------------------------------------------------


class TestListPage:
    def test_round_trip(self):
        data = {
            "Items": [{"ID": "p1", "Name": "A"}, {"ID": "p2", "Name": "B"}],
            "Meta": {
                "Page": 1,
                "PageSize": 20,
                "TotalCount": 2,
                "TotalPages": 1,
                "ItemRange": [1, 2],
            },
        }
        page = ListPage[Product].model_validate(data)
        assert len(page.Items) == 2
        assert page.Meta.TotalCount == 2
        assert page.Meta.ItemRange == [1, 2]

    def test_empty_page(self):
        page = ListPage[Product]()
        assert page.Items == []
        assert page.Meta.TotalCount == 0

    def test_meta_with_facets(self):
        meta = MetaWithFacets.model_validate({
            "Page": 1,
            "PageSize": 20,
            "TotalCount": 100,
            "TotalPages": 5,
            "ItemRange": [1, 20],
            "Facets": [
                {"Name": "Color", "XpPath": "xp.Color", "Values": [{"Value": "Red", "Count": 15}]},
            ],
        })
        assert len(meta.Facets) == 1
        assert meta.Facets[0].Values[0].Count == 15
