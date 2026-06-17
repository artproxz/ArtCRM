import json
import unittest
from dataclasses import replace
from decimal import Decimal

from backend.app.catalog import (
    CatalogFilter,
    CatalogItem,
    CatalogItemStatus,
    CatalogSourceType,
    CatalogSort,
    CatalogViewMode,
    InMemoryCatalogRepository,
    PriceRecord,
    PriceType,
    StockBalance,
    build_catalog_item_dedup_key,
    build_price_record_key,
    build_stock_balance_key,
    normalize_attribute_key,
    normalize_attribute_value,
)


class CatalogStockPriceFoundationTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryCatalogRepository()

    def test_catalog_item_internal_serialization_is_json_friendly(self):
        item = _pressure_gauge_16()

        payload = item.to_dict()
        encoded = json.dumps(payload, ensure_ascii=False)

        self.assertIn("Манометр показывающий ТМ-510", encoded)
        self.assertEqual(payload["package_size"], "1")
        self.assertEqual(payload["attributes"]["diameter"], "100")
        self.assertEqual(payload["source"], "rosma")
        self.assertEqual(payload["external_refs"], {"source_row": "synthetic"})

    def test_catalog_item_public_serialization_hides_source_and_external_refs(self):
        payload = _pressure_gauge_16().to_public_dict()

        self.assertNotIn("source", payload)
        self.assertNotIn("external_refs", payload)
        self.assertNotIn("ref", payload)

    def test_stock_and_price_serialization_are_json_friendly(self):
        stock = StockBalance("stock-1", "pg-16", "main", Decimal("5.5"), Decimal("1"), source="stock_file")
        price = PriceRecord("price-1", "pg-16", "base", "rub", Decimal("100.50"), vat_rate=Decimal("20"))

        encoded = json.dumps({"stock": stock.to_dict(), "price": price.to_dict()})

        self.assertIn('"quantity_available": "5.5"', encoded)
        self.assertIn('"amount": "100.50"', encoded)

    def test_public_stock_and_price_hide_source_external_refs_and_supplier_ref(self):
        stock = StockBalance("stock-1", "pg-16", "main", 5, source="stock_file", external_refs={"row": "1"})
        price = PriceRecord(
            "price-1",
            "pg-16",
            "base",
            "rub",
            100,
            supplier_ref="supplier:demo",
            source="imported",
            external_refs={"row": "1"},
        )

        self.assertNotIn("source", stock.to_public_dict())
        self.assertNotIn("external_refs", stock.to_public_dict())
        self.assertNotIn("source", price.to_public_dict())
        self.assertNotIn("external_refs", price.to_public_dict())
        self.assertNotIn("supplier_ref", price.to_public_dict())

    def test_create_get_list_update_and_archive_catalog_item(self):
        item = _pressure_gauge_16()

        created = self.repository.create_catalog_item(item)
        updated = self.repository.update_catalog_item(item.with_updates(description="updated description"))
        archived = self.repository.archive_catalog_item(item.catalog_item_id)

        self.assertTrue(created.success)
        self.assertEqual(self.repository.get_catalog_item("pg-16").value.catalog_item_id, "pg-16")
        self.assertEqual(len(self.repository.list_catalog_items()), 1)
        self.assertTrue(updated.success)
        self.assertEqual(updated.value.description, "updated description")
        self.assertTrue(archived.success)
        self.assertEqual(archived.value.status, CatalogItemStatus.ARCHIVED)

    def test_duplicate_catalog_item_id_is_rejected(self):
        self.repository.create_catalog_item(_pressure_gauge_16())

        result = self.repository.create_catalog_item(_pressure_gauge_16())

        self.assertFalse(result.success)
        self.assertEqual(result.error.code.value, "conflict")

    def test_direct_catalog_item_status_update_is_denied(self):
        item = _pressure_gauge_16()
        self.repository.create_catalog_item(item)

        result = self.repository.update_catalog_item(item.with_status(CatalogItemStatus.ARCHIVED))

        self.assertFalse(result.success)
        self.assertEqual(result.error.code.value, "invalid_state_transition")
        self.assertEqual(self.repository.get_catalog_item("pg-16").value.status, CatalogItemStatus.ACTIVE)

    def test_dedup_prefers_article_internal_supplier_then_name_brand_manufacturer(self):
        article_item = _pressure_gauge_16()
        internal_item = replace(article_item, catalog_item_id="internal", article=None, internal_code="INT-1")
        supplier_item = replace(article_item, catalog_item_id="supplier", article=None, internal_code=None, supplier_code="SUP-1")
        name_item = replace(article_item, catalog_item_id="name", article=None, internal_code=None, supplier_code=None, sku=None)

        self.assertEqual(build_catalog_item_dedup_key(article_item), "article:TM-510-1.6")
        self.assertEqual(build_catalog_item_dedup_key(internal_item), "internal_code:INT-1")
        self.assertEqual(build_catalog_item_dedup_key(supplier_item), "supplier_code:SUP-1")
        self.assertIn("name:манометр показывающий", build_catalog_item_dedup_key(name_item))

    def test_find_catalog_item_by_dedup_key(self):
        item = _pressure_gauge_16()
        self.repository.create_catalog_item(item)

        found = self.repository.find_catalog_item_by_dedup_key(build_catalog_item_dedup_key(item))

        self.assertTrue(found.success)
        self.assertEqual(found.value.catalog_item_id, "pg-16")

    def test_stock_balance_cannot_be_created_for_unknown_catalog_item(self):
        result = self.repository.create_stock_balance(StockBalance("stock-1", "missing", "main", 5))

        self.assertFalse(result.success)
        self.assertEqual(result.error.code.value, "not_found")

    def test_price_record_cannot_be_created_for_unknown_catalog_item(self):
        result = self.repository.create_price_record(PriceRecord("price-1", "missing", "base", "RUB", 100))

        self.assertFalse(result.success)
        self.assertEqual(result.error.code.value, "not_found")

    def test_stock_balance_links_to_catalog_item_and_dedups_by_key(self):
        self.repository.create_catalog_item(_pressure_gauge_16())
        stock = StockBalance("stock-1", "pg-16", "main", 5)

        result = self.repository.create_stock_balance(stock)
        listed = self.repository.list_stock_balances_by_item("pg-16")
        found = self.repository.find_stock_balance_by_key(build_stock_balance_key(stock))

        self.assertTrue(result.success)
        self.assertEqual(stock.catalog_item_ref, "catalog_item:pg-16")
        self.assertEqual(listed.value, (stock,))
        self.assertEqual(found.value.stock_balance_id, "stock-1")

    def test_price_record_links_to_catalog_item_and_dedups_by_key(self):
        self.repository.create_catalog_item(_pressure_gauge_16())
        price = PriceRecord("price-1", "pg-16", "base", "rub", 100, supplier_ref="supplier:demo")

        result = self.repository.create_price_record(price)
        listed = self.repository.list_price_records_by_item("pg-16")
        found = self.repository.find_price_record_by_key(build_price_record_key(price))

        self.assertTrue(result.success)
        self.assertEqual(price.catalog_item_ref, "catalog_item:pg-16")
        self.assertEqual(listed.value, (price,))
        self.assertEqual(found.value.price_record_id, "price-1")

    def test_direct_stock_balance_catalog_item_id_update_is_denied(self):
        self._seed_catalog()
        stock = self.repository.get_stock_balance("stock-pg16").value

        result = self.repository.update_stock_balance(stock.with_updates(catalog_item_id="thermo-100"))

        self.assertFalse(result.success)
        self.assertEqual(result.error.details["reason"], "catalog_item_id_change_forbidden")
        self.assertEqual(self.repository.get_stock_balance("stock-pg16").value.catalog_item_id, "pg-16")

    def test_direct_price_record_catalog_item_id_update_is_denied(self):
        self._seed_catalog()
        price = self.repository.get_price_record("price-pg16").value

        result = self.repository.update_price_record(price.with_updates(catalog_item_id="thermo-100"))

        self.assertFalse(result.success)
        self.assertEqual(result.error.details["reason"], "catalog_item_id_change_forbidden")
        self.assertEqual(self.repository.get_price_record("price-pg16").value.catalog_item_id, "pg-16")

    def test_search_catalog_items_matches_name_article_sku_supplier_aliases_and_terms(self):
        self._seed_catalog()

        by_article = self.repository.search_catalog_items("TM-510-1.6")
        by_alias = self.repository.search_catalog_items("rosma pressure")

        self.assertEqual(by_article[0].catalog_item_id, "pg-16")
        self.assertEqual(by_alias[0].catalog_item_id, "pg-16")

    def test_catalog_filter_filters_by_product_type(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(CatalogFilter(product_types=("pressure_gauge",)))

        self.assertEqual({item.catalog_item_id for item in result}, {"pg-16", "pg-25"})

    def test_catalog_filter_filters_by_category_group_and_subgroup(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(
            CatalogFilter(categories=("pressure instruments",), groups=("gauges",), subgroups=("pressure gauges",))
        )

        self.assertEqual({item.catalog_item_id for item in result}, {"pg-16", "pg-25"})

    def test_catalog_filter_filters_by_brand_and_manufacturer(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(CatalogFilter(brands=("artmatica",), manufacturers=("artmatica",)))

        self.assertEqual([item.catalog_item_id for item in result], ["thermowell-100"])

    def test_catalog_filter_filters_by_status_source_and_unit(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(
            CatalogFilter(statuses=("active",), sources=("rosma",), units=("шт",))
        )

        self.assertEqual({item.catalog_item_id for item in result}, {"pg-16", "pg-25", "thermo-100"})

    def test_catalog_filter_filters_by_availability(self):
        self._seed_catalog()

        in_stock = self.repository.filter_catalog_items(CatalogFilter(has_stock=True))
        out_of_stock = self.repository.filter_catalog_items(CatalogFilter(has_stock=False))
        min_qty = self.repository.filter_catalog_items(CatalogFilter(min_available_quantity=Decimal("4")))

        self.assertEqual({item.catalog_item_id for item in in_stock}, {"pg-16", "thermo-100"})
        self.assertEqual({item.catalog_item_id for item in out_of_stock}, {"pg-25", "thermowell-100"})
        self.assertEqual([item.catalog_item_id for item in min_qty], ["pg-16"])

    def test_catalog_filter_filters_by_price_presence(self):
        self._seed_catalog()

        has_price = self.repository.filter_catalog_items(CatalogFilter(has_price=True))
        no_price = self.repository.filter_catalog_items(CatalogFilter(has_price=False))

        self.assertEqual({item.catalog_item_id for item in has_price}, {"pg-16", "pg-25", "thermo-100"})
        self.assertEqual([item.catalog_item_id for item in no_price], ["thermowell-100"])

    def test_catalog_filter_filters_by_price_range_currency_price_type_and_supplier(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(
            CatalogFilter(
                min_price=Decimal("120"),
                max_price=Decimal("220"),
                currency="rub",
                price_type="base",
                supplier_refs=("supplier:demo",),
            )
        )

        self.assertEqual({item.catalog_item_id for item in result}, {"pg-25", "thermo-100"})

    def test_catalog_filter_filters_by_attribute_key_value(self):
        self._seed_catalog()

        by_thread = self.repository.filter_catalog_items(CatalogFilter(attribute_filters={"thread": "M20x1,5"}))
        by_length = self.repository.filter_catalog_items(CatalogFilter(attribute_filters={"length": "100"}))

        self.assertEqual({item.catalog_item_id for item in by_thread}, {"pg-16", "pg-25"})
        self.assertEqual({item.catalog_item_id for item in by_length}, {"thermo-100", "thermowell-100"})

    def test_attribute_helpers_normalize_keys_and_values(self):
        self.assertEqual(normalize_attribute_key(" Connection-Type "), "connection_type")
        self.assertEqual(normalize_attribute_value("  M20x1,5  "), "m20x1,5")
        self.assertEqual(normalize_attribute_value(Decimal("1.50")), "1.50")

    def test_catalog_sort_sorts_by_name(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(sort=CatalogSort.NAME)

        self.assertEqual([item.catalog_item_id for item in result], ["thermowell-100", "pg-16", "pg-25", "thermo-100"])

    def test_catalog_sort_sorts_by_article(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(sort=CatalogSort.ARTICLE)

        self.assertEqual([item.article for item in result], ["BT-100", "GL-100", "TM-510-1.6", "TM-510-2.5"])

    def test_catalog_sort_sorts_by_availability(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(sort=CatalogSort.AVAILABILITY)

        self.assertEqual([item.catalog_item_id for item in result[:2]], ["pg-16", "thermo-100"])

    def test_catalog_sort_sorts_by_price(self):
        self._seed_catalog()

        result = self.repository.filter_catalog_items(sort=CatalogSort.PRICE)

        self.assertEqual([item.catalog_item_id for item in result], ["pg-16", "pg-25", "thermo-100", "thermowell-100"])

    def test_catalog_view_mode_dashboard_returns_card_like_projections(self):
        self._seed_catalog()

        cards = self.repository.list_catalog_cards(CatalogFilter(product_types=("pressure_gauge",)))
        payload = cards[0].to_dict()

        self.assertEqual(CatalogViewMode.DASHBOARD.value, "dashboard")
        self.assertIn("display_name", payload)
        self.assertIn("availability_summary", payload)
        self.assertIn("price_summary", payload)
        self.assertIn("highlights", payload)
        self.assertEqual(payload["availability_summary"]["has_stock"], True)

    def test_catalog_view_mode_reference_returns_list_row_like_projections(self):
        self._seed_catalog()

        rows = self.repository.list_catalog_reference_rows(CatalogFilter(product_types=("pressure_gauge",)), sort=CatalogSort.ARTICLE)
        payload = rows[0].to_dict()

        self.assertEqual(CatalogViewMode.REFERENCE.value, "reference")
        self.assertIn("internal_code", payload)
        self.assertIn("available_quantity", payload)
        self.assertIn("base_price", payload)
        self.assertEqual(payload["article"], "TM-510-1.6")

    def test_facet_summary_counts_categories_product_types_brands_manufacturers_statuses_sources_availability(self):
        self._seed_catalog()

        facets = self.repository.build_catalog_facets().to_dict()

        self.assertEqual(facets["categories"]["Pressure Instruments"], 2)
        self.assertEqual(facets["product_types"]["pressure_gauge"], 2)
        self.assertEqual(facets["brands"]["ROSMA"], 3)
        self.assertEqual(facets["manufacturers"]["Artmatica"], 1)
        self.assertEqual(facets["statuses"]["active"], 4)
        self.assertEqual(facets["sources"]["rosma"], 3)
        self.assertEqual(facets["availability"]["in_stock"], 2)
        self.assertEqual(facets["availability"]["reserved"], 1)
        self.assertEqual(facets["availability"]["unavailable"], 1)

    def _seed_catalog(self):
        for item in (_pressure_gauge_16(), _pressure_gauge_25(), _thermometer_100(), _thermowell_100()):
            self.repository.create_catalog_item(item)
        for stock in (
            StockBalance("stock-pg16", "pg-16", "main", Decimal("5"), Decimal("0"), "шт", source="stock_file"),
            StockBalance("stock-pg25", "pg-25", "main", Decimal("0"), Decimal("2"), "шт", source="stock_file"),
            StockBalance("stock-thermo", "thermo-100", "main", Decimal("3"), Decimal("0"), "шт", source="stock_file"),
        ):
            self.repository.create_stock_balance(stock)
        for price in (
            PriceRecord("price-pg16", "pg-16", "base", "RUB", Decimal("100"), supplier_ref="supplier:demo", source="imported"),
            PriceRecord("price-pg25", "pg-25", "base", "RUB", Decimal("150"), supplier_ref="supplier:demo", source="imported"),
            PriceRecord("price-thermo", "thermo-100", "base", "RUB", Decimal("200"), supplier_ref="supplier:demo", source="imported"),
        ):
            self.repository.create_price_record(price)


def _pressure_gauge_16():
    return CatalogItem(
        catalog_item_id="pg-16",
        sku="PG-16",
        article="TM-510-1.6",
        supplier_code="R-001",
        internal_code="INT-PG-16",
        name="Манометр показывающий ТМ-510 0-1,6 МПа М20х1,5",
        product_type="pressure_gauge",
        category="Pressure Instruments",
        group="Gauges",
        subgroup="Pressure Gauges",
        brand="ROSMA",
        manufacturer="ROSMA",
        product_line="TM-510",
        description="Synthetic catalog item",
        unit="шт",
        package_size=Decimal("1"),
        attributes={
            "measurement_range": "0-1,6 МПа",
            "thread": "M20x1,5",
            "accuracy_class": "1.5",
            "diameter": Decimal("100"),
        },
        aliases=("rosma pressure", "tm510"),
        search_terms=("манометр", "pressure gauge"),
        status=CatalogItemStatus.ACTIVE,
        source=CatalogSourceType.ROSMA,
        external_refs={"source_row": "synthetic"},
    )


def _pressure_gauge_25():
    return CatalogItem(
        catalog_item_id="pg-25",
        sku="PG-25",
        article="TM-510-2.5",
        supplier_code="R-002",
        internal_code="INT-PG-25",
        name="Манометр показывающий ТМ-510 0-2,5 МПа М20х1,5",
        product_type="pressure_gauge",
        category="Pressure Instruments",
        group="Gauges",
        subgroup="Pressure Gauges",
        brand="ROSMA",
        manufacturer="ROSMA",
        product_line="TM-510",
        unit="шт",
        attributes={"measurement_range": "0-2,5 МПа", "thread": "M20x1,5", "accuracy_class": "1.5"},
        status="active",
        source="rosma",
    )


def _thermometer_100():
    return CatalogItem(
        catalog_item_id="thermo-100",
        sku="BT-100",
        article="BT-100",
        supplier_code="T-001",
        internal_code="INT-T-100",
        name="Термометр биметаллический 0-160 C L=100 G1/2",
        product_type="bimetal_thermometer",
        category="Temperature Instruments",
        group="Thermometers",
        subgroup="Bimetal Thermometers",
        brand="ROSMA",
        manufacturer="ROSMA",
        unit="шт",
        attributes={"temperature_range": "0-160 C", "length": "100", "thread": "G1/2"},
        status="active",
        source="rosma",
    )


def _thermowell_100():
    return CatalogItem(
        catalog_item_id="thermowell-100",
        sku="GL-100",
        article="GL-100",
        supplier_code="A-001",
        internal_code="INT-GL-100",
        name="Гильза защитная для термометра L=100",
        product_type="thermowell",
        category="Accessories",
        group="Thermowells",
        subgroup="Thermowells",
        brand="Artmatica",
        manufacturer="Artmatica",
        unit="шт",
        attributes={"length": "100", "material": "stainless"},
        status="active",
        source="imported",
    )


if __name__ == "__main__":
    unittest.main()
