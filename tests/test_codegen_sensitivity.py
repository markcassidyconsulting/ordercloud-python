"""Tests for the codegen's path-parameter sensitivity registry and gate.

Imports only the jinja-free codegen modules: CI installs ``.[dev]``, which
does not include jinja2.  The renderer tests skip when jinja2 is absent.
"""

from __future__ import annotations

import pytest

from tools.codegen.ir import OperationDef, ParamDef, ResourceDef
from tools.codegen.sensitivity import (
    NOT_SENSITIVE_PATH_PARAMS,
    REDACTION_MARKER,
    SENSITIVE_PATH_PARAMS,
    redacted_path_params,
    spec_name,
    validate_path_param_classification,
)
from tools.codegen.transformer import transform

SENSITIVE_IMPORT = "from ..http import SensitivePath"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def path_param(api_name: str, python_name: str) -> ParamDef:
    """A path parameter as the parser builds it."""
    return ParamDef(
        name=python_name,
        python_type="str",
        description="",
        location="path",
        api_name=api_name if api_name != python_name else None,
    )


def operation(operation_id: str, path_template: str, *params: ParamDef) -> OperationDef:
    return OperationDef(
        method_name="get",
        http_method="get",
        path_template=path_template,
        summary="",
        description="",
        path_params=list(params),
        operation_id=operation_id,
    )


def resource(*ops: OperationDef) -> ResourceDef:
    return ResourceDef(
        class_name="WidgetsResource",
        module_name="widgets",
        attribute_name="widgets",
        module_docstring="",
        class_docstring="",
        operations=list(ops),
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_sets_are_disjoint(self):
        assert SENSITIVE_PATH_PARAMS.isdisjoint(NOT_SENSITIVE_PATH_PARAMS)

    def test_known_credentials_are_sensitive(self):
        assert {"verificationCode", "invitationID"} <= SENSITIVE_PATH_PARAMS

    def test_marker_is_safe_inside_a_string_literal(self):
        assert REDACTION_MARKER
        for ch in "{}'\"\\":
            assert ch not in REDACTION_MARKER

    def test_spec_name_prefers_api_name(self):
        assert spec_name(path_param("widgetID", "widget_id")) == "widgetID"
        assert spec_name(path_param("key", "key")) == "key"

    def test_redacted_path_params_are_the_not_log_safe_ones(self):
        cleared = path_param("buyerID", "buyer_id")
        cleared.log_safe = True
        secret = path_param("verificationCode", "verification_code")
        op = operation("X.Get", "/x/{buyer_id}/{verification_code}", cleared, secret)
        assert redacted_path_params(op) == [secret]


# ---------------------------------------------------------------------------
# Classification gate
# ---------------------------------------------------------------------------


class TestValidateClassification:
    def test_fully_classified_is_clean(self):
        res = resource(
            operation("Widgets.Get", "/widgets/{widget_id}", path_param("widgetID", "widget_id")),
            operation("Widgets.Reset", "/reset/{code}", path_param("code", "code")),
        )
        errors = validate_path_param_classification(
            [res], sensitive=frozenset({"code"}), not_sensitive=frozenset({"widgetID"})
        )
        assert errors == []

    def test_unclassified_name_is_one_error_naming_it_and_its_operation(self):
        res = resource(
            operation("Widgets.Get", "/widgets/{widget_id}", path_param("widgetID", "widget_id")),
            operation("Widgets.Token", "/tokens/{token_id}", path_param("tokenID", "token_id")),
        )
        errors = validate_path_param_classification(
            [res], sensitive=frozenset(), not_sensitive=frozenset({"widgetID"})
        )
        assert len(errors) == 1
        assert "'tokenID'" in errors[0]
        assert "Widgets.Token" in errors[0]
        assert "Widgets.Get" not in errors[0]

    def test_unclassified_error_lists_every_operation_using_the_name(self):
        res = resource(
            operation("Widgets.Get", "/a/{token_id}", path_param("tokenID", "token_id")),
            operation("Widgets.Delete", "/b/{token_id}", path_param("tokenID", "token_id")),
        )
        errors = validate_path_param_classification(
            [res], sensitive=frozenset(), not_sensitive=frozenset()
        )
        assert len(errors) == 1
        assert "Widgets.Delete, Widgets.Get" in errors[0]

    def test_name_in_both_sets_is_an_error(self):
        res = resource(
            operation("Widgets.Get", "/widgets/{widget_id}", path_param("widgetID", "widget_id"))
        )
        errors = validate_path_param_classification(
            [res], sensitive=frozenset({"widgetID"}), not_sensitive=frozenset({"widgetID"})
        )
        assert len(errors) == 1
        assert "'widgetID' is in both" in errors[0]

    def test_stale_entry_is_an_error(self):
        res = resource(
            operation("Widgets.Get", "/widgets/{widget_id}", path_param("widgetID", "widget_id"))
        )
        errors = validate_path_param_classification(
            [res], sensitive=frozenset({"goneID"}), not_sensitive=frozenset({"widgetID"})
        )
        assert len(errors) == 1
        assert "'goneID' is classified but not in the spec" in errors[0]

    def test_names_match_exactly(self):
        """``creditcardID`` and ``creditCardID`` are distinct spec names."""
        res = resource(
            operation(
                "Me.GetCard",
                "/me/cards/{creditcard_id}",
                path_param("creditcardID", "creditcard_id"),
            )
        )
        errors = validate_path_param_classification(
            [res], sensitive=frozenset(), not_sensitive=frozenset({"creditCardID"})
        )
        assert any("'creditcardID' is not classified" in e for e in errors)


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------


class TestTransformerClassification:
    def test_unclassified_param_stays_redacted_and_imports_sensitive_path(self):
        param = path_param("tokenID", "token_id")
        res = resource(operation("Widgets.Token", "/tokens/{token_id}", param))
        _, enriched = transform({}, {}, {"Widgets": res})
        assert param.log_safe is False
        assert SENSITIVE_IMPORT in enriched[0].import_lines

    def test_sensitive_param_is_redacted(self):
        param = path_param("verificationCode", "verification_code")
        res = resource(operation("X.Reset", "/password/reset/{verification_code}", param))
        _, enriched = transform({}, {}, {"X": res})
        assert param.log_safe is False
        assert SENSITIVE_IMPORT in enriched[0].import_lines

    def test_cleared_param_is_log_safe_without_import(self):
        param = path_param("productID", "product_id")
        res = resource(operation("Products.Get", "/products/{product_id}", param))
        _, enriched = transform({}, {}, {"Products": res})
        assert param.log_safe is True
        assert SENSITIVE_IMPORT not in enriched[0].import_lines


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


class TestPathExpr:
    @pytest.fixture(autouse=True)
    def _path_expr(self):
        pytest.importorskip("jinja2")
        from tools.codegen.renderer import _path_expr

        self.path_expr = _path_expr

    def test_constant_path(self):
        assert self.path_expr(operation("Me.Get", "/me")) == '"/me"'

    def test_cleared_path_is_a_plain_fstring(self):
        param = path_param("productID", "product_id")
        param.log_safe = True
        op = operation("Products.Get", "/products/{product_id}", param)
        assert self.path_expr(op) == 'f"/products/{product_id}"'

    def test_redacted_path_is_wrapped(self):
        cleared = path_param("productCollectionID", "product_collection_id")
        cleared.log_safe = True
        secret = path_param("invitationID", "invitation_id")
        op = operation(
            "Me.AcceptProductCollectionInvitation",
            "/me/productcollections/{product_collection_id}/invitations/accept/{invitation_id}",
            cleared,
            secret,
        )
        assert self.path_expr(op) == (
            "SensitivePath("
            'wire=f"/me/productcollections/{product_collection_id}/invitations/accept/{invitation_id}", '
            'log_form=f"/me/productcollections/{product_collection_id}/invitations/accept/***")'
        )

    def test_fully_redacted_log_form_is_a_plain_string(self):
        op = operation(
            "X.Reset",
            "/password/reset/{verification_code}",
            path_param("verificationCode", "verification_code"),
        )
        assert self.path_expr(op) == (
            'SensitivePath(wire=f"/password/reset/{verification_code}", '
            'log_form="/password/reset/***")'
        )

    def test_missing_placeholder_raises(self):
        op = operation(
            "X.Reset", "/password/reset/{code}", path_param("verificationCode", "verification_code")
        )
        with pytest.raises(ValueError, match="verification_code"):
            self.path_expr(op)
