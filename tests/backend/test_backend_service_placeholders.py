import unittest

from backend.app.analogs import AnalogLookupRequest, AnalogRuleService
from backend.app.audit import AuditEvent, AuditService, MatcherExecutionAuditRef
from backend.app.catalog import CatalogLookupRequest, CatalogService
from backend.app.delivery import DeliveryEstimateRequest, DeliveryEstimateService
from backend.app.matcher import CatalogMatchRequest, CatalogMatcherService
from backend.app.pricing import ManagerItemDiscount, PricingService
from backend.app.related_components import RelatedComponentService, RelatedComponentValidationRequest
from backend.app.stock import StockLookupRequest, StockService
from backend.app.supplier_quotes import SupplierQuoteRequest, SupplierQuoteResponse, SupplierQuoteService

DEMO_CATALOG_ITEM_ID = "demo-catalog-item-id"
DEMO_REQUEST_ID = "demo-request-id"
DEMO_STOCK_SNAPSHOT_ID = "demo-stock-snapshot-id"
DEMO_CART_ITEM_REF = "demo-cart-item-ref"
DEMO_MANUFACTURER_SCOPE = "demo-manufacturer-scope"
DEMO_PRODUCT_TYPE = "demo-product-type"


class BackendServicePlaceholderTests(unittest.TestCase):
    def assert_not_implemented(self, method, *args, **kwargs):
        with self.assertRaises(NotImplementedError):
            method(*args, **kwargs)

    def test_catalog_service_placeholders_raise_not_implemented(self):
        service = CatalogService()
        request = CatalogLookupRequest(manufacturer_scope=DEMO_MANUFACTURER_SCOPE)

        self.assert_not_implemented(service.get_active_publication, DEMO_MANUFACTURER_SCOPE)
        self.assert_not_implemented(service.find_catalog_candidates, request)
        self.assert_not_implemented(service.get_catalog_item, DEMO_CATALOG_ITEM_ID)

    def test_stock_service_placeholders_raise_not_implemented(self):
        service = StockService()
        request = StockLookupRequest(
            catalog_item_id=DEMO_CATALOG_ITEM_ID,
            manufacturer_scope=DEMO_MANUFACTURER_SCOPE,
        )

        self.assert_not_implemented(service.get_latest_stock_snapshot, DEMO_MANUFACTURER_SCOPE)
        self.assert_not_implemented(service.get_stock_for_catalog_item, request)

    def test_pricing_service_placeholders_raise_not_implemented(self):
        service = PricingService()
        discount = ManagerItemDiscount(reason="demo-discount-reason")

        self.assert_not_implemented(service.get_catalog_item_price, DEMO_CATALOG_ITEM_ID)
        self.assert_not_implemented(service.create_cart_price_snapshot, DEMO_CATALOG_ITEM_ID, 1.0)
        self.assert_not_implemented(service.apply_manager_discount, DEMO_CART_ITEM_REF, discount)

    def test_delivery_service_placeholders_raise_not_implemented(self):
        service = DeliveryEstimateService()
        request = DeliveryEstimateRequest(catalog_item_id=DEMO_CATALOG_ITEM_ID)

        self.assert_not_implemented(service.estimate_delivery, request)
        self.assert_not_implemented(
            service.apply_supplier_confirmed_delivery,
            DEMO_CART_ITEM_REF,
            "demo-delivery-label",
        )

    def test_supplier_quote_service_placeholders_raise_not_implemented(self):
        service = SupplierQuoteService()
        request = SupplierQuoteRequest(manufacturer_scope=DEMO_MANUFACTURER_SCOPE)
        response = SupplierQuoteResponse(supplier_quote_request_id=DEMO_REQUEST_ID)

        self.assert_not_implemented(service.create_quote_request_draft, request)
        self.assert_not_implemented(service.register_supplier_response, response)

    def test_matcher_service_placeholders_raise_not_implemented(self):
        service = CatalogMatcherService()
        request = CatalogMatchRequest(
            request_id=DEMO_REQUEST_ID,
            request_position_ref=DEMO_REQUEST_ID,
            product_type=DEMO_PRODUCT_TYPE,
            manufacturer_scope=DEMO_MANUFACTURER_SCOPE,
        )

        self.assert_not_implemented(service.match_position, request)

    def test_analog_service_placeholders_raise_not_implemented(self):
        service = AnalogRuleService()
        request = AnalogLookupRequest(product_type=DEMO_PRODUCT_TYPE)

        self.assert_not_implemented(service.find_analog_candidates, request)

    def test_related_component_service_placeholders_raise_not_implemented(self):
        service = RelatedComponentService()
        request = RelatedComponentValidationRequest(parent_position_ref=DEMO_REQUEST_ID)

        self.assert_not_implemented(service.validate_related_components, request)

    def test_audit_service_placeholders_raise_not_implemented(self):
        service = AuditService()
        event = AuditEvent(
            entity_type="demo-entity",
            entity_id=DEMO_REQUEST_ID,
            event_type="demo-event",
        )
        matcher_execution_ref = MatcherExecutionAuditRef(
            matcher_execution_id=DEMO_REQUEST_ID,
            request_position_ref=DEMO_REQUEST_ID,
        )

        self.assert_not_implemented(service.record_event, event)
        self.assert_not_implemented(service.record_matcher_execution, matcher_execution_ref)


if __name__ == "__main__":
    unittest.main()
