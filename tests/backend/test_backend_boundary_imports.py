import importlib
import unittest


BACKEND_MODULES = [
    "backend",
    "backend.app",
    "backend.app.catalog",
    "backend.app.stock",
    "backend.app.pricing",
    "backend.app.delivery",
    "backend.app.supplier_quotes",
    "backend.app.matcher",
    "backend.app.analogs",
    "backend.app.related_components",
    "backend.app.audit",
]

EXPECTED_EXPORTS = {
    "backend.app.catalog": "CatalogService",
    "backend.app.stock": "StockService",
    "backend.app.pricing": "PricingService",
    "backend.app.delivery": "DeliveryEstimateService",
    "backend.app.supplier_quotes": "SupplierQuoteService",
    "backend.app.matcher": "CatalogMatcherService",
    "backend.app.analogs": "AnalogRuleService",
    "backend.app.related_components": "RelatedComponentService",
    "backend.app.audit": "AuditService",
}


class BackendBoundaryImportTests(unittest.TestCase):
    def test_backend_modules_import_without_external_setup(self):
        for module_name in BACKEND_MODULES:
            with self.subTest(module_name=module_name):
                module = importlib.import_module(module_name)
                self.assertEqual(module.__name__, module_name)

    def test_expected_boundary_service_exports_are_available(self):
        for module_name, export_name in EXPECTED_EXPORTS.items():
            with self.subTest(module_name=module_name, export_name=export_name):
                module = importlib.import_module(module_name)
                self.assertTrue(hasattr(module, export_name))


if __name__ == "__main__":
    unittest.main()
