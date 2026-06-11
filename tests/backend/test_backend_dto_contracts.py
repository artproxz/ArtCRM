import unittest

from backend.app.analogs import AnalogDecision, AnalogLookupRequest, AnalogLookupResult, AnalogRuleRef
from backend.app.audit import AuditEvent, MatcherExecutionAuditRef, PublicationEvent
from backend.app.catalog import CatalogItemRef, CatalogLookupRequest, CatalogLookupResult, CatalogPublicationRef
from backend.app.delivery import CartItemDeliveryEstimate, DeliveryEstimateRequest, DeliveryEstimateResult
from backend.app.matcher import (
    CatalogMatchDecision,
    CatalogMatchRequest,
    CatalogMatchResponse,
    MatcherExecutionRef,
    MatcherValidationError,
)
from backend.app.pricing import CatalogItemPriceRef, CartItemPriceSnapshot, ManagerItemDiscount, PriceSourceRef
from backend.app.related_components import (
    RelatedComponentDecision,
    RelatedComponentRuleRef,
    RelatedComponentValidationRequest,
    RelatedComponentValidationResult,
)
from backend.app.stock import StockLookupRequest, StockLookupResult, StockSnapshotRef, StockStatus
from backend.app.supplier_quotes import (
    SupplierQuoteRequest,
    SupplierQuoteRequestItem,
    SupplierQuoteResponse,
    SupplierQuoteResponseItem,
    SupplierQuoteStatus,
)

DEMO_CATALOG_ITEM_ID = "demo-catalog-item-id"
DEMO_REQUEST_ID = "demo-request-id"
DEMO_AGENT_RUN_REF = "demo-agent-run-ref"
DEMO_STOCK_SNAPSHOT_ID = "demo-stock-snapshot-id"
DEMO_CART_ITEM_REF = "demo-cart-item-ref"
DEMO_MANUFACTURER_SCOPE = "demo-manufacturer-scope"
DEMO_PRODUCT_TYPE = "demo-product-type"


def enum_values(enum_cls):
    return {item.value for item in enum_cls}


class BackendEnumContractTests(unittest.TestCase):
    def test_catalog_match_decision_values(self):
        self.assertEqual(
            enum_values(CatalogMatchDecision),
            {"exact", "compatible_exact", "analog_candidate", "needs_review", "no_match", "blocked"},
        )

    def test_stock_status_values(self):
        self.assertEqual(
            enum_values(StockStatus),
            {
                "in_stock",
                "out_of_stock",
                "reserved_only",
                "expected",
                "unknown",
                "quote_based",
                "manual_check_required",
                "unresolved_stock_reference",
            },
        )

    def test_supplier_quote_status_values(self):
        self.assertEqual(
            enum_values(SupplierQuoteStatus),
            {"draft", "sent", "waiting_response", "answered", "closed", "canceled"},
        )

    def test_related_component_decision_values(self):
        self.assertEqual(
            enum_values(RelatedComponentDecision),
            {"accepted_candidate", "needs_review", "blocked", "duplicate_suppressed", "not_requested"},
        )

    def test_analog_decision_values(self):
        self.assertEqual(
            enum_values(AnalogDecision),
            {"not_requested", "unavailable", "candidate_found", "blocked", "needs_review"},
        )


class BackendDtoConstructionTests(unittest.TestCase):
    def test_catalog_dtos_can_be_constructed(self):
        item_ref = CatalogItemRef(catalog_item_id=DEMO_CATALOG_ITEM_ID)
        publication_ref = CatalogPublicationRef(catalog_publication_id=DEMO_CATALOG_ITEM_ID)
        request = CatalogLookupRequest(manufacturer_scope=DEMO_MANUFACTURER_SCOPE)
        result = CatalogLookupResult(catalog_publication_ref=publication_ref, candidates=[item_ref])

        self.assertEqual(item_ref.catalog_item_id, DEMO_CATALOG_ITEM_ID)
        self.assertEqual(request.manufacturer_scope, DEMO_MANUFACTURER_SCOPE)
        self.assertEqual(result.candidates, [item_ref])

    def test_stock_dtos_can_be_constructed(self):
        snapshot_ref = StockSnapshotRef(stock_snapshot_id=DEMO_STOCK_SNAPSHOT_ID)
        request = StockLookupRequest(
            catalog_item_id=DEMO_CATALOG_ITEM_ID,
            manufacturer_scope=DEMO_MANUFACTURER_SCOPE,
            stock_snapshot_ref=snapshot_ref,
        )
        result = StockLookupResult(stock_snapshot_ref=snapshot_ref)

        self.assertEqual(request.catalog_item_id, DEMO_CATALOG_ITEM_ID)
        self.assertEqual(result.stock_status, StockStatus.UNKNOWN)

    def test_pricing_dtos_can_be_constructed(self):
        price_source = PriceSourceRef(price_source_id=DEMO_CATALOG_ITEM_ID)
        price_ref = CatalogItemPriceRef(
            catalog_item_price_id=DEMO_CATALOG_ITEM_ID,
            catalog_item_id=DEMO_CATALOG_ITEM_ID,
            price_source_ref=price_source,
        )
        discount = ManagerItemDiscount(reason="demo-discount-reason")
        snapshot = CartItemPriceSnapshot(
            cart_item_ref=DEMO_CART_ITEM_REF,
            catalog_item_id=DEMO_CATALOG_ITEM_ID,
            catalog_item_price_ref=price_ref,
            manager_discount=discount,
        )

        self.assertEqual(snapshot.cart_item_ref, DEMO_CART_ITEM_REF)
        self.assertEqual(snapshot.catalog_item_price_ref, price_ref)

    def test_delivery_dtos_can_be_constructed(self):
        request = DeliveryEstimateRequest(catalog_item_id=DEMO_CATALOG_ITEM_ID)
        estimate = CartItemDeliveryEstimate(cart_item_ref=DEMO_CART_ITEM_REF)
        result = DeliveryEstimateResult(estimate=estimate)

        self.assertEqual(request.catalog_item_id, DEMO_CATALOG_ITEM_ID)
        self.assertEqual(result.estimate, estimate)

    def test_supplier_quote_dtos_can_be_constructed(self):
        request_item = SupplierQuoteRequestItem(catalog_item_id=DEMO_CATALOG_ITEM_ID)
        request = SupplierQuoteRequest(manufacturer_scope=DEMO_MANUFACTURER_SCOPE, items=[request_item])
        response_item = SupplierQuoteResponseItem(catalog_item_id=DEMO_CATALOG_ITEM_ID)
        response = SupplierQuoteResponse(supplier_quote_request_id=DEMO_REQUEST_ID, items=[response_item])

        self.assertEqual(request.status, SupplierQuoteStatus.DRAFT)
        self.assertEqual(response.items, [response_item])

    def test_matcher_dtos_can_be_constructed(self):
        request = CatalogMatchRequest(
            request_id=DEMO_REQUEST_ID,
            request_position_ref=DEMO_REQUEST_ID,
            product_type=DEMO_PRODUCT_TYPE,
            manufacturer_scope=DEMO_MANUFACTURER_SCOPE,
        )
        error = MatcherValidationError(error_code="demo-error", error_message="demo-error-message")
        execution_ref = MatcherExecutionRef(matcher_execution_id=DEMO_REQUEST_ID)
        response = CatalogMatchResponse(
            request_id=DEMO_REQUEST_ID,
            errors=[error],
            matcher_execution_ref=execution_ref,
        )

        self.assertEqual(request.request_id, DEMO_REQUEST_ID)
        self.assertEqual(response.decision, CatalogMatchDecision.NEEDS_REVIEW)

    def test_analog_dtos_can_be_constructed(self):
        rule_ref = AnalogRuleRef(analog_rule_id=DEMO_REQUEST_ID)
        request = AnalogLookupRequest(product_type=DEMO_PRODUCT_TYPE)
        result = AnalogLookupResult(analog_rule_refs=[rule_ref])

        self.assertEqual(request.product_type, DEMO_PRODUCT_TYPE)
        self.assertEqual(result.decision, AnalogDecision.UNAVAILABLE)

    def test_related_component_dtos_can_be_constructed(self):
        rule_ref = RelatedComponentRuleRef(related_component_rule_id=DEMO_REQUEST_ID)
        request = RelatedComponentValidationRequest(parent_position_ref=DEMO_REQUEST_ID)
        result = RelatedComponentValidationResult(rule_refs=[rule_ref])

        self.assertEqual(request.parent_position_ref, DEMO_REQUEST_ID)
        self.assertEqual(result.decision, RelatedComponentDecision.NEEDS_REVIEW)

    def test_audit_dtos_can_be_constructed(self):
        audit_event = AuditEvent(
            entity_type="demo-entity",
            entity_id=DEMO_REQUEST_ID,
            event_type="demo-event",
        )
        publication_event = PublicationEvent(
            entity_type="demo-entity",
            entity_id=DEMO_REQUEST_ID,
            new_status="demo-status",
        )
        matcher_audit_ref = MatcherExecutionAuditRef(
            matcher_execution_id=DEMO_REQUEST_ID,
            agent_run_ref=DEMO_AGENT_RUN_REF,
        )

        self.assertEqual(audit_event.entity_id, DEMO_REQUEST_ID)
        self.assertEqual(publication_event.new_status, "demo-status")
        self.assertEqual(matcher_audit_ref.agent_run_ref, DEMO_AGENT_RUN_REF)


if __name__ == "__main__":
    unittest.main()
