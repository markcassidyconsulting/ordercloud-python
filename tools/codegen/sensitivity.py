"""Path-parameter sensitivity registry.

The SDK logs the path of every request.  Some path parameters carry values
that work as credentials, and those values must never reach a log line.
Every path-parameter name in the spec must appear in exactly one of the two
sets below; the codegen refuses to generate while any name is unclassified,
classified twice, or classified but absent from the spec.

Decision rule:

- **SENSITIVE**: anyone who reads the value from a log could use it to
  authenticate, obtain a token, or perform an account action without the
  account owner's own credentials.
- **NOT SENSITIVE**: record identifiers that grant nothing without the
  caller's own authorisation.
- When uncertain, choose SENSITIVE.

``NOT_SENSITIVE_PATH_PARAMS`` is an allowlist: a path parameter whose name is
not on it is written to the log as ``REDACTION_MARKER``.

Known limit: classification is by name.  A future spec could reuse an
already-cleared name for a credential-bearing value, and this gate cannot see
that.  Reviewing the spec diff at each spec bump is the control.
"""

from __future__ import annotations

from collections.abc import Iterable

from .ir import OperationDef, ParamDef, ResourceDef

__all__ = [
    "REDACTION_MARKER",
    "SENSITIVE_PATH_PARAMS",
    "NOT_SENSITIVE_PATH_PARAMS",
    "spec_name",
    "redacted_path_params",
    "validate_path_param_classification",
]

# Written to the log in place of a redacted path value.  It is spliced into a
# generated string literal, so it must contain no braces, quotes or backslash.
REDACTION_MARKER = "***"

# Spec (camelCase) names whose values are credentials.
SENSITIVE_PATH_PARAMS: frozenset[str] = frozenset(
    {
        # PUT /password/reset/{verificationCode}: the code sets a new password
        # on the account it was issued for.
        "verificationCode",
        # The spec (Me.CreateGroupOrderInvitation): "Contributors may request
        # an access token with the invitation ID", and
        # POST /grouporders/{invitationID}/token returns an AccessToken.
        "invitationID",
    }
)

# Spec (camelCase) names whose values may be logged: record identifiers and
# enum values that grant nothing without the caller's own authorisation.
NOT_SENSITIVE_PATH_PARAMS: frozenset[str] = frozenset(
    {
        "addressID",
        # OAuth client identifier.  RFC 6749 section 2.2: "The client identifier
        # is not a secret".
        "apiClientID",
        # Identifies a secret record; the secret value only ever travels in a
        # response body.
        "apiClientSecretID",
        "approvalRuleID",
        "bundleID",
        "bundleItemID",
        "buyerGroupID",
        "buyerID",
        "catalogID",
        "categoryID",
        "costCenterID",
        # Credit-card record IDs, not card numbers.  The spec spells it both
        # ways (/buyers/.../creditcards/{creditCardID}, /me/creditcards/{creditcardID}).
        "creditCardID",
        "creditcardID",
        "deliveryConfigID",
        # OrderDirection enum value.
        "direction",
        "discountID",
        "eventID",
        "impersonationConfigID",
        "incrementorID",
        "integrationEventID",
        "inventoryRecordID",
        # Key of an xp index (DELETE /xpindices/{thingType}/{key}).
        "key",
        "lineItemID",
        "localeID",
        "messageSenderID",
        "newBuyerID",
        "openidconnectID",
        "optionID",
        "orderID",
        "paymentID",
        "priceScheduleID",
        "productCollectionID",
        "productFacetID",
        "productID",
        # Applies a promotion to an order; it does not authenticate anything.
        "promoCode",
        "promotionID",
        "returnID",
        "securityProfileID",
        "shipmentID",
        "specID",
        "spendingAccountID",
        "subscriptionID",
        "subscriptionItemID",
        "supplierID",
        # XpThingType enum value.
        "thingType",
        # Payment transaction record ID.
        "transactionID",
        "userGroupID",
        "userID",
        "variantID",
        "webhookID",
    }
)


def spec_name(param: ParamDef) -> str:
    """Return the parameter's name as the spec spells it."""
    return param.api_name or param.name


def redacted_path_params(op: OperationDef) -> list[ParamDef]:
    """Return the operation's path parameters that must not be logged."""
    return [p for p in op.path_params if not p.log_safe]


def validate_path_param_classification(
    resources: Iterable[ResourceDef],
    *,
    sensitive: frozenset[str] = SENSITIVE_PATH_PARAMS,
    not_sensitive: frozenset[str] = NOT_SENSITIVE_PATH_PARAMS,
) -> list[str]:
    """Check that every path-parameter name in the spec is classified exactly once.

    Returns a list of error messages (empty if everything is correct).
    """
    errors: list[str] = []

    used_by: dict[str, set[str]] = {}
    for resource in resources:
        for op in resource.operations:
            for param in op.path_params:
                used_by.setdefault(spec_name(param), set()).add(op.operation_id)

    for name in sorted(sensitive & not_sensitive):
        errors.append(
            f"Path parameter '{name}' is in both SENSITIVE_PATH_PARAMS and "
            f"NOT_SENSITIVE_PATH_PARAMS"
        )

    classified = sensitive | not_sensitive
    for name in sorted(used_by.keys() - classified):
        errors.append(
            f"Path parameter '{name}' is not classified (used by "
            f"{', '.join(sorted(used_by[name]))}); add it to SENSITIVE_PATH_PARAMS "
            f"or NOT_SENSITIVE_PATH_PARAMS in tools/codegen/sensitivity.py"
        )

    for name in sorted(classified - used_by.keys()):
        errors.append(f"Path parameter '{name}' is classified but not in the spec")

    return errors
