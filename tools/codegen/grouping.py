"""Schema-to-module grouping map.

Every schema in the OpenAPI spec must appear in exactly one group (or
in MANUAL_SCHEMAS).  The codegen asserts completeness at generation time.

Groups follow the Phase 1 convention: related models share a file,
named after the primary model (e.g. ``product.py`` holds Product,
Inventory, Variant, VariantInventory, etc.).
"""

from __future__ import annotations

__all__ = [
    "SCHEMA_GROUPS",
    "MANUAL_SCHEMAS",
    "RE_EXPORTS",
]

# Schemas that are defined manually and must NOT be generated.
# These live in shared.py (pagination types) or errors.py.
MANUAL_SCHEMAS: set[str] = {
    "Meta",
    "MetaWithFacets",
    "ListFacet",
    "ListFacetValue",
    "Error",
}

# Backward-compatibility re-exports.  When schemas move between modules
# (e.g. to break circular imports), the old module should still export
# them so existing import paths don't break.
# Maps module name → list of (source_module, name) pairs to re-export.
RE_EXPORTS: dict[str, list[tuple[str, str]]] = {
    "order": [
        ("misc", "OrderDirection"),
        ("misc", "OrderStatus"),
    ],
}

# Maps module filename (without .py) to the list of schema names it contains.
# Order within a group matters: dependencies must come before dependants.
SCHEMA_GROUPS: dict[str, list[str]] = {
    # === Core commerce ===
    "product": [
        "Inventory",
        "VariantInventory",
        "VariantSpec",
        "VariantOverrides",
        "Variant",
        "AdHocProduct",
        "ProductSupplier",
        "Product",
    ],
    "bundle": [
        "Bundle",
    ],
    "order": [
        "OrderApprovalInfo",
        "ApprovalInfo",
        "OrderApproval",
        "OrderPromotion",
        "ShipMethodSelection",
        "OrderShipMethodSelection",
        "OrderSplitResult",
        "OrderSubmitResponse",
        "OrderSubmitForApprovalResponse",
        "OrderApprovedResponse",
        "OrderCalculateResponse",
        "LineItemOverride",
        "ExtendedLineItem",
        "OrderWorksheet",
        "Order",
    ],
    "line_item": [
        "BundleItems",
        "LineItem",
    ],
    "line_item_types": [
        "LineItemProduct",
        "LineItemVariant",
        "LineItemSpec",
    ],
    "order_return": [
        "OrderReturnItem",
        "OrderReturnApproval",
        "OrderReturn",
    ],
    "buyer": [
        "BuyerPriceBreak",
        "BuyerPriceSchedule",
        "ProductSeller",
        "BuyerAddress",
        "BuyerCreditCard",
        "BuyerProduct",
        "BuyerSupplier",
        "BuyerGroup",
        "Buyer",
    ],
    "user": [
        "Locale",
        "UserOrderMoveOption",
        "MeBuyer",
        "MeSeller",
        "MeSupplier",
        "OrderUser",
        "MeUser",
        "User",
    ],
    "catalog": [
        "Catalog",
    ],
    "category": [
        "Category",
    ],
    "address": [
        "Address",
    ],
    "supplier": [
        "SupplierBuyer",
        "Supplier",
    ],
    # === Pricing & promotions ===
    "price_schedule": [
        "PriceMarkupType",
        "PriceBreak",
        "PriceSchedule",
    ],
    "spec": [
        "SpecOption",
        "Spec",
    ],
    "promotion": [
        "PromotionOverride",
        "PromotionIntegration",
        "AddedPromo",
        "RemovedPromo",
        "EligiblePromotion",
        "RefreshPromosResponse",
        "Promotion",
    ],
    "payment": [
        "PaymentType",
        "PaymentTransaction",
        "Payment",
    ],
    "discount": [
        "DiscountBreak",
        "DiscountedPrices",
        "Discount",
    ],
    # === Fulfillment ===
    "shipment": [
        "ShipMethod",
        "ShipEstimateItem",
        "ShipEstimate",
        "ShipEstimateResponse",
        "ShipmentItem",
        "Shipment",
    ],
    # === Organization & accounts ===
    "cost_center": [
        "CostCenter",
    ],
    "credit_card": [
        "CreditCard",
    ],
    "spending_account": [
        "SpendingAccount",
    ],
    "inventory_record": [
        "InventoryIntegration",
        "InventoryRecord",
    ],
    "user_group": [
        "UserGroup",
    ],
    # === Security & auth ===
    "security": [
        "PasswordConfig",
        "ImpersonationConfig",
        "SecurityProfile",
    ],
    "api_client": [
        "ApiClientSecret",
        "ApiClientSecretCreateResponse",
        "ApiClient",
    ],
    "approval": [
        "ApprovalStatus",
        "ApprovalType",
        "ApprovalRule",
        "SellerApprovalRule",
    ],
    # === Subscriptions ===
    "subscription": [
        "SubscriptionInterval",
        "SubscriptionPayment",
        "SubscriptionIntegration",
        "SubscriptionIntegrationResponse",
        "Subscription",
    ],
    # === Messaging & integrations ===
    "message_sender": [
        "MessageType",
        "MessageSenderConfig",
        "MessageSender",
    ],
    "webhook": [
        "WebhookRoute",
        "Webhook",
    ],
    "integration": [
        "IntegrationEventType",
        "IntegrationEvent",
        "TrackingEventType",
        "TrackingEvent",
    ],
    "open_id_connect": [
        "OpenIdConnect",
    ],
    # === Delivery & sync infrastructure ===
    "delivery": [
        "KafkaConfig",
        "HttpConfig",
        "EventHubConfig",
        "AzureBlobConfig",
        "AzureTableConfig",
        "CosmosDbConfig",
        "MailchimpConfig",
        "ContentHubConfig",
        "SearchIngestionContent",
        "SearchIngestionHttpContent",
        "SearchIngestion",
        "DeliveryTargets",
        "DeliveryConfig",
        "SendEvent",
        "DiscoverEvent",
        "ErrorConfig",
    ],
    "sync": [
        "EntitySyncConfig",
        "OrderSyncConfig",
        "ProductSyncConfig",
        "SyncAdminUser",
        "SyncBuyer",
        "SyncBuyerUser",
        "SyncBuyerUserGroup",
        "SyncCategory",
        "SyncInventoryRecord",
        "SyncProduct",
        "SyncSupplier",
        "SyncSupplierUser",
    ],
    # === Product collections ===
    "product_collection": [
        "ProductCollectionEntry",
        "ProductCollectionProduct",
        "ProductCollectionBuyerProduct",
        "ProductCollectionInvitation",
        "ProductCollection",
    ],
    # === Assignments (cross-cutting) ===
    "assignments": [
        "AddressAssignment",
        "ApiClientAssignment",
        "BundleAssignment",
        "BundleCatalogAssignment",
        "BundleProductAssignment",
        "CatalogAssignment",
        "CategoryAssignment",
        "CategoryBundleAssignment",
        "CategoryProductAssignment",
        "CostCenterAssignment",
        "CreditCardAssignment",
        "DiscountAssignment",
        "InventoryRecordAssignment",
        "LocaleAssignment",
        "MessageCCListenerAssignment",
        "MessageSenderAssignment",
        "ProductAssignment",
        "ProductCatalogAssignment",
        "PromotionAssignment",
        "SecurityProfileAssignment",
        "SpecProductAssignment",
        "SpendingAccountAssignment",
        "UserGroupAssignment",
    ],
    # === Miscellaneous ===
    "auth_models": [
        "AccessToken",
        "AccessTokenBasic",
        "ImpersonateTokenRequest",
        "OneTimePasswordRequest",
        "PasswordReset",
        "PasswordResetRequest",
        "TokenPasswordReset",
    ],
    "misc": [
        "AccessLevel",
        "ApiRole",
        "CommerceRole",
        "OrderDirection",
        "OrderStatus",
        "PartyType",
        "SearchType",
        "XpThingType",
        "Incrementor",
        "XpIndex",
        "ProductFacet",
        "GroupOrderInvitation",
    ],
}


def validate_completeness(spec_schemas: set[str]) -> list[str]:
    """Check that every spec schema is accounted for.

    Returns a list of error messages (empty if everything is correct).
    """
    errors: list[str] = []

    # Collect all assigned schemas.
    assigned: set[str] = set(MANUAL_SCHEMAS)
    seen_in_group: dict[str, str] = {}
    for module, schemas in SCHEMA_GROUPS.items():
        for name in schemas:
            if name in seen_in_group:
                errors.append(
                    f"Schema '{name}' appears in both "
                    f"'{seen_in_group[name]}' and '{module}'"
                )
            seen_in_group[name] = module
            assigned.add(name)

    # Check for missing schemas.
    missing = spec_schemas - assigned
    if missing:
        errors.append(f"Schemas not assigned to any group: {sorted(missing)}")

    # Check for extra schemas (in grouping but not in spec).
    extra = assigned - spec_schemas
    if extra:
        errors.append(f"Schemas in grouping but not in spec: {sorted(extra)}")

    return errors
