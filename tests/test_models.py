"""Tests for Pydantic model serialisation and behaviour."""

from __future__ import annotations


from ordercloud.models import (
    Address,
    Buyer,
    Catalog,
    Category,
    ListPage,
    MetaWithFacets,
    Product,
)
from ordercloud.models.order import Order, OrderDirection, OrderStatus
from ordercloud.models.line_item import LineItem
from ordercloud.models.payment import Payment, PaymentType
from ordercloud.models.price_schedule import PriceSchedule
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
        assert p.id == "x"
        assert p.name == "Widget"

    def test_exclude_none(self):
        """model_dump(exclude_none=True) drops None fields."""
        p = Product(ID="x")
        dumped = p.model_dump(exclude_none=True)
        assert "id" in dumped
        assert "name" not in dumped
        assert "description" not in dumped


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
        assert p.id == "prod-1"
        assert p.quantity_multiplier == 5
        assert p.spec_count == 3
        assert p.xp == {"color": "red", "weight": 1.5}

        dumped = p.model_dump(exclude_none=True)
        assert dumped["quantity_multiplier"] == 5
        assert dumped["xp"]["color"] == "red"

    def test_defaults(self):
        p = Product()
        assert p.quantity_multiplier == 1
        assert p.spec_count == 0
        assert p.variant_count == 0
        assert p.xp is None

    def test_inventory_embedded(self):
        data = {
            "ID": "p1",
            "Inventory": {"Enabled": True, "QuantityAvailable": 50},
        }
        p = Product.model_validate(data)
        assert p.inventory is not None
        assert p.inventory.enabled is True


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
        assert o.status == OrderStatus.Unsubmitted
        assert o.line_item_count == 3
        assert o.subtotal == 99.99

    def test_enum_serialises_as_string(self):
        o = Order(Status=OrderStatus.Open)
        dumped = o.model_dump(exclude_none=True)
        assert dumped["status"] == "Open"

    def test_embedded_user(self):
        data = {
            "ID": "ord-1",
            "FromUser": {"ID": "user-1", "Username": "buyer@test.com"},
        }
        o = Order.model_validate(data)
        assert o.from_user is not None
        assert o.from_user.username == "buyer@test.com"

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
        assert o.billing_address.city == "Portland"


class TestLineItemModel:
    def test_round_trip(self):
        data = {
            "ID": "li-1",
            "ProductID": "prod-1",
            "Quantity": 3,
            "xp": {"gift_wrap": True},
        }
        li = LineItem.model_validate(data)
        assert li.product_id == "prod-1"
        assert li.quantity == 3

    def test_defaults(self):
        li = LineItem()
        assert li.quantity == 1


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
        assert dumped["street1"] == "123 Main St"
        assert dumped["country"] == "US"


class TestBuyerModel:
    def test_round_trip(self):
        data = {"ID": "buyer-1", "Name": "Acme Corp", "Active": True}
        b = Buyer.model_validate(data)
        assert b.name == "Acme Corp"


class TestCatalogModel:
    def test_round_trip(self):
        data = {"ID": "cat-1", "Name": "Spring 2026", "Active": True}
        c = Catalog.model_validate(data)
        assert c.name == "Spring 2026"


class TestCategoryModel:
    def test_round_trip(self):
        data = {"ID": "category-1", "Name": "Electronics", "Active": True}
        c = Category.model_validate(data)
        assert c.name == "Electronics"


# ---------------------------------------------------------------------------
# Phase 2 model sampling
# ---------------------------------------------------------------------------


class TestPhase2Models:
    def test_payment_with_enum(self):
        data = {"ID": "pay-1", "Type": "CreditCard", "Amount": 99.99}
        p = Payment.model_validate(data)
        assert p.type == PaymentType.CreditCard
        dumped = p.model_dump(exclude_none=True)
        assert dumped["type"] == "CreditCard"

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
        assert len(ps.price_breaks) == 2
        assert ps.price_breaks[1].price == 8.0

    def test_promotion(self):
        data = {
            "ID": "promo-1",
            "Code": "SAVE10",
            "Name": "10% Off",
            "Active": True,
        }
        p = Promotion.model_validate(data)
        assert p.code == "SAVE10"

    def test_shipment(self):
        data = {
            "ID": "ship-1",
            "BuyerID": "buyer-1",
            "DateShipped": "2026-04-13T12:00:00Z",
        }
        s = Shipment.model_validate(data)
        assert s.buyer_id == "buyer-1"

    def test_security_profile(self):
        data = {"ID": "sp-1", "Name": "Buyer Admin", "Roles": ["BuyerAdmin", "AddressAdmin"]}
        sp = SecurityProfile.model_validate(data)
        assert "BuyerAdmin" in sp.roles


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
# Typed xp generics
# ---------------------------------------------------------------------------


class TestTypedXpGenerics:
    def test_unparameterized_accepts_dict(self):
        """Product without type param still accepts dict xp (backward compat)."""
        p = Product(Name="Widget", xp={"color": "red", "size": 10})  # PascalCase construction OK
        assert p.xp == {"color": "red", "size": 10}

    def test_unparameterized_round_trip(self):
        data = {"Name": "Widget", "xp": {"custom": True}}
        p = Product.model_validate(data)
        assert p.xp == {"custom": True}
        dumped = p.model_dump(exclude_none=True)
        assert dumped["xp"] == {"custom": True}

    def test_parameterized_with_pydantic_model(self):
        from pydantic import BaseModel

        class MyXp(BaseModel):
            color: str
            size: int

        p = Product[MyXp](Name="Widget", xp=MyXp(color="red", size=10))
        assert p.xp.color == "red"
        assert p.xp.size == 10

    def test_parameterized_serialisation(self):
        from pydantic import BaseModel

        class MyXp(BaseModel):
            color: str

        p = Product[MyXp](Name="Widget", xp=MyXp(color="blue"))
        dumped = p.model_dump(exclude_none=True)
        assert dumped["xp"] == {"color": "blue"}

    def test_parameterized_deserialisation(self):
        from pydantic import BaseModel

        class MyXp(BaseModel):
            color: str
            size: int

        data = {"Name": "Widget", "xp": {"color": "red", "size": 10}}
        p = Product[MyXp].model_validate(data)
        assert isinstance(p.xp, MyXp)
        assert p.xp.color == "red"

    def test_xp_none_by_default(self):
        p = Product(Name="Widget")
        assert p.xp is None

    def test_order_with_xp(self):
        o = Order(xp={"priority": "high"})
        assert o.xp == {"priority": "high"}


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
        assert len(page.items) == 2
        assert page.meta.total_count == 2
        assert page.meta.item_range == [1, 2]

    def test_empty_page(self):
        page = ListPage[Product]()
        assert page.items == []
        assert page.meta.total_count == 0

    def test_meta_with_facets(self):
        meta = MetaWithFacets.model_validate(
            {
                "Page": 1,
                "PageSize": 20,
                "TotalCount": 100,
                "TotalPages": 5,
                "ItemRange": [1, 20],
                "Facets": [
                    {
                        "Name": "Color",
                        "XpPath": "xp.Color",
                        "Values": [{"Value": "Red", "Count": 15}],
                    },
                ],
            }
        )
        assert len(meta.facets) == 1
        assert meta.facets[0].values[0].count == 15
