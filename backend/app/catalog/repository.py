from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Generic, Iterable, Optional, TypeVar

from backend.app.common import ApiError, conflict_error, invalid_state_transition_error, not_found_error

from .filtering import CatalogFilter, CatalogQuery, CatalogSort, coerce_catalog_sort, filter_value_matches
from .models import CatalogCardView, CatalogFacetSummary, CatalogItem, CatalogListRow, PriceRecord, StockBalance
from .normalization import (
    build_catalog_item_dedup_key,
    build_price_record_key,
    build_stock_balance_key,
    decimal_to_json,
    normalize_attribute_key,
    normalize_currency,
    normalize_name,
    normalize_unit,
)
from .statuses import CatalogItemStatus, PriceType


T = TypeVar("T")


@dataclass(frozen=True)
class RepositoryResult(Generic[T]):
    success: bool
    value: Optional[T] = None
    error: Optional[ApiError] = None

    @property
    def is_error(self) -> bool:
        return not self.success


class InMemoryCatalogRepository:
    """Deterministic in-memory catalog store for backend foundation tests."""

    def __init__(self) -> None:
        self._items: dict[str, CatalogItem] = {}
        self._stock_balances: dict[str, StockBalance] = {}
        self._price_records: dict[str, PriceRecord] = {}

    def create_catalog_item(self, item: CatalogItem) -> RepositoryResult[CatalogItem]:
        if item.catalog_item_id in self._items:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=item.ref, details={"reason": "catalog_item_id_already_exists"}),
            )
        self._items[item.catalog_item_id] = item
        return RepositoryResult(success=True, value=item)

    def get_catalog_item(self, catalog_item_id: str) -> RepositoryResult[CatalogItem]:
        item = self._items.get(str(catalog_item_id))
        if item is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"catalog_item:{catalog_item_id}", details={"entity": "CatalogItem"}),
            )
        return RepositoryResult(success=True, value=item)

    def list_catalog_items(self) -> tuple[CatalogItem, ...]:
        return tuple(sorted(self._items.values(), key=lambda item: item.created_at))

    def update_catalog_item(self, item: CatalogItem) -> RepositoryResult[CatalogItem]:
        existing = self._items.get(item.catalog_item_id)
        if existing is None:
            return RepositoryResult(success=False, error=not_found_error(entity_ref=item.ref, details={"entity": "CatalogItem"}))
        if item.status != existing.status:
            return RepositoryResult(
                success=False,
                error=invalid_state_transition_error(
                    entity_ref=item.ref,
                    from_state=existing.status.value,
                    to_state=item.status.value,
                    details={"reason": "direct_status_update_forbidden"},
                ),
            )
        self._items[item.catalog_item_id] = item
        return RepositoryResult(success=True, value=item)

    def archive_catalog_item(self, catalog_item_id: str) -> RepositoryResult[CatalogItem]:
        existing = self.get_catalog_item(catalog_item_id)
        if not existing.success:
            return existing
        item = existing.value
        assert item is not None
        archived = item.with_status(CatalogItemStatus.ARCHIVED)
        self._items[archived.catalog_item_id] = archived
        return RepositoryResult(success=True, value=archived)

    def find_catalog_item_by_dedup_key(self, key: str) -> RepositoryResult[CatalogItem]:
        for item in self._items.values():
            if build_catalog_item_dedup_key(item) == key:
                return RepositoryResult(success=True, value=item)
        return RepositoryResult(success=False, error=not_found_error(entity_ref=key, details={"entity": "CatalogItem"}))

    def search_catalog_items(
        self,
        query: str,
        *,
        sort: CatalogSort | str = CatalogSort.RELEVANCE,
    ) -> tuple[CatalogItem, ...]:
        return self.filter_catalog_items(CatalogFilter(query=query), sort=sort)

    def filter_catalog_items(
        self,
        filters: CatalogFilter | CatalogQuery | None = None,
        *,
        sort: CatalogSort | str = CatalogSort.RELEVANCE,
    ) -> tuple[CatalogItem, ...]:
        query: Optional[CatalogQuery] = filters if isinstance(filters, CatalogQuery) else None
        active_filter = query.filters if query else (filters or CatalogFilter())
        active_sort = query.sort if query else coerce_catalog_sort(sort)
        items = [item for item in self._items.values() if self._matches_filter(item, active_filter)]
        sorted_items = self._sort_items(items, active_sort, active_filter.query)
        if query:
            start = query.offset
            end = None if query.limit is None else start + query.limit
            sorted_items = sorted_items[start:end]
        return tuple(sorted_items)

    def list_catalog_cards(
        self,
        filters: CatalogFilter | CatalogQuery | None = None,
        *,
        sort: CatalogSort | str = CatalogSort.RELEVANCE,
    ) -> tuple[CatalogCardView, ...]:
        return tuple(self._to_card(item) for item in self.filter_catalog_items(filters, sort=sort))

    def list_catalog_reference_rows(
        self,
        filters: CatalogFilter | CatalogQuery | None = None,
        *,
        sort: CatalogSort | str = CatalogSort.RELEVANCE,
    ) -> tuple[CatalogListRow, ...]:
        return tuple(self._to_reference_row(item) for item in self.filter_catalog_items(filters, sort=sort))

    def build_catalog_facets(self, items: Optional[Iterable[CatalogItem]] = None) -> CatalogFacetSummary:
        selected_items = tuple(items if items is not None else self._items.values())
        return CatalogFacetSummary(
            categories=_count_values(item.category for item in selected_items),
            product_types=_count_values(item.product_type for item in selected_items),
            brands=_count_values(item.brand for item in selected_items),
            manufacturers=_count_values(item.manufacturer for item in selected_items),
            statuses=_count_values(item.status.value for item in selected_items),
            sources=_count_values(item.source.value if item.source else None for item in selected_items),
            availability=_count_values(self._availability_bucket(item) for item in selected_items),
        )

    def create_stock_balance(self, balance: StockBalance) -> RepositoryResult[StockBalance]:
        item_result = self.get_catalog_item(balance.catalog_item_id)
        if not item_result.success:
            return RepositoryResult(success=False, error=item_result.error)
        if balance.stock_balance_id in self._stock_balances:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=balance.ref, details={"reason": "stock_balance_id_already_exists"}),
            )
        self._stock_balances[balance.stock_balance_id] = balance
        return RepositoryResult(success=True, value=balance)

    def get_stock_balance(self, stock_balance_id: str) -> RepositoryResult[StockBalance]:
        balance = self._stock_balances.get(str(stock_balance_id))
        if balance is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"stock_balance:{stock_balance_id}", details={"entity": "StockBalance"}),
            )
        return RepositoryResult(success=True, value=balance)

    def list_stock_balances_by_item(self, catalog_item_id: str) -> RepositoryResult[tuple[StockBalance, ...]]:
        item_result = self.get_catalog_item(catalog_item_id)
        if not item_result.success:
            return RepositoryResult(success=False, error=item_result.error)
        balances = tuple(
            sorted(
                (balance for balance in self._stock_balances.values() if balance.catalog_item_id == str(catalog_item_id)),
                key=lambda balance: balance.updated_at,
            )
        )
        return RepositoryResult(success=True, value=balances)

    def update_stock_balance(self, balance: StockBalance) -> RepositoryResult[StockBalance]:
        existing = self._stock_balances.get(balance.stock_balance_id)
        if existing is None:
            return RepositoryResult(success=False, error=not_found_error(entity_ref=balance.ref, details={"entity": "StockBalance"}))
        if balance.catalog_item_id != existing.catalog_item_id:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=balance.ref, details={"reason": "catalog_item_id_change_forbidden"}),
            )
        self._stock_balances[balance.stock_balance_id] = balance
        return RepositoryResult(success=True, value=balance)

    def find_stock_balance_by_key(self, key: str) -> RepositoryResult[StockBalance]:
        for balance in self._stock_balances.values():
            if build_stock_balance_key(balance) == key:
                return RepositoryResult(success=True, value=balance)
        return RepositoryResult(success=False, error=not_found_error(entity_ref=key, details={"entity": "StockBalance"}))

    def create_price_record(self, record: PriceRecord) -> RepositoryResult[PriceRecord]:
        item_result = self.get_catalog_item(record.catalog_item_id)
        if not item_result.success:
            return RepositoryResult(success=False, error=item_result.error)
        if record.price_record_id in self._price_records:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=record.ref, details={"reason": "price_record_id_already_exists"}),
            )
        self._price_records[record.price_record_id] = record
        return RepositoryResult(success=True, value=record)

    def get_price_record(self, price_record_id: str) -> RepositoryResult[PriceRecord]:
        record = self._price_records.get(str(price_record_id))
        if record is None:
            return RepositoryResult(
                success=False,
                error=not_found_error(entity_ref=f"price_record:{price_record_id}", details={"entity": "PriceRecord"}),
            )
        return RepositoryResult(success=True, value=record)

    def list_price_records_by_item(self, catalog_item_id: str) -> RepositoryResult[tuple[PriceRecord, ...]]:
        item_result = self.get_catalog_item(catalog_item_id)
        if not item_result.success:
            return RepositoryResult(success=False, error=item_result.error)
        records = tuple(
            sorted(
                (record for record in self._price_records.values() if record.catalog_item_id == str(catalog_item_id)),
                key=lambda record: record.created_at,
            )
        )
        return RepositoryResult(success=True, value=records)

    def update_price_record(self, record: PriceRecord) -> RepositoryResult[PriceRecord]:
        existing = self._price_records.get(record.price_record_id)
        if existing is None:
            return RepositoryResult(success=False, error=not_found_error(entity_ref=record.ref, details={"entity": "PriceRecord"}))
        if record.catalog_item_id != existing.catalog_item_id:
            return RepositoryResult(
                success=False,
                error=conflict_error(entity_ref=record.ref, details={"reason": "catalog_item_id_change_forbidden"}),
            )
        self._price_records[record.price_record_id] = record
        return RepositoryResult(success=True, value=record)

    def find_price_record_by_key(self, key: str) -> RepositoryResult[PriceRecord]:
        for record in self._price_records.values():
            if build_price_record_key(record) == key:
                return RepositoryResult(success=True, value=record)
        return RepositoryResult(success=False, error=not_found_error(entity_ref=key, details={"entity": "PriceRecord"}))

    def _matches_filter(self, item: CatalogItem, filters: CatalogFilter) -> bool:
        if filters.query and filters.query not in self._search_blob(item):
            return False
        if filters.product_types and normalize_name(item.product_type) not in filters.product_types:
            return False
        if filters.categories and normalize_name(item.category) not in filters.categories:
            return False
        if filters.groups and normalize_name(item.group) not in filters.groups:
            return False
        if filters.subgroups and normalize_name(item.subgroup) not in filters.subgroups:
            return False
        if filters.brands and normalize_name(item.brand) not in filters.brands:
            return False
        if filters.manufacturers and normalize_name(item.manufacturer) not in filters.manufacturers:
            return False
        if filters.units and normalize_unit(item.unit) not in filters.units:
            return False
        if filters.statuses and item.status not in filters.statuses:
            return False
        if filters.sources and item.source not in filters.sources:
            return False
        if filters.has_stock is not None and self._has_stock(item) != filters.has_stock:
            return False
        if filters.min_available_quantity is not None and self._available_quantity(item) < filters.min_available_quantity:
            return False
        matching_prices = self._matching_prices(item, filters)
        if filters.has_price is not None and bool(matching_prices) != filters.has_price:
            return False
        if filters.min_price is not None and not any(record.amount >= filters.min_price for record in matching_prices):
            return False
        if filters.max_price is not None and not any(record.amount <= filters.max_price for record in matching_prices):
            return False
        if filters.supplier_refs:
            supplier_refs = {normalize_name(record.supplier_ref) for record in self._price_records_for_item(item)}
            if not any(normalize_name(ref) in supplier_refs for ref in filters.supplier_refs):
                return False
        for key, expected in filters.attribute_filters.items():
            attribute_key = normalize_attribute_key(key)
            if attribute_key not in item.attributes:
                return False
            if not filter_value_matches(item.attributes[attribute_key], expected):
                return False
        return True

    def _matching_prices(self, item: CatalogItem, filters: CatalogFilter) -> tuple[PriceRecord, ...]:
        records = self._price_records_for_item(item)
        if filters.currency:
            records = tuple(record for record in records if record.currency == normalize_currency(filters.currency))
        if filters.price_type:
            records = tuple(record for record in records if record.price_type == filters.price_type)
        return records

    def _sort_items(self, items: list[CatalogItem], sort: CatalogSort, query: Optional[str]) -> list[CatalogItem]:
        if sort == CatalogSort.NAME:
            return sorted(items, key=lambda item: (normalize_name(item.name) or "", item.catalog_item_id))
        if sort == CatalogSort.ARTICLE:
            return sorted(items, key=lambda item: (item.article or "", item.name))
        if sort == CatalogSort.AVAILABILITY:
            return sorted(items, key=lambda item: (self._available_quantity(item), item.name), reverse=True)
        if sort == CatalogSort.PRICE:
            return sorted(items, key=lambda item: (self._lowest_price_amount(item) is None, self._lowest_price_amount(item) or Decimal("0"), item.name))
        if sort == CatalogSort.UPDATED_AT:
            return sorted(items, key=lambda item: item.updated_at, reverse=True)
        return sorted(items, key=lambda item: (-self._relevance_score(item, query), normalize_name(item.name) or ""))

    def _search_blob(self, item: CatalogItem) -> str:
        values = (
            item.name,
            item.normalized_name,
            item.article,
            item.sku,
            item.supplier_code,
            item.internal_code,
            item.product_type,
            item.category,
            item.brand,
            item.manufacturer,
            *item.aliases,
            *item.search_terms,
        )
        return " ".join(value for value in (normalize_name(value) for value in values if value) if value)

    def _relevance_score(self, item: CatalogItem, query: Optional[str]) -> int:
        if not query:
            return 0
        score = 0
        for value in (item.article, item.sku, item.supplier_code, item.internal_code):
            if normalize_name(value) == query:
                score += 10
        if query in (item.normalized_name or ""):
            score += 5
        if query in self._search_blob(item):
            score += 1
        return score

    def _to_card(self, item: CatalogItem) -> CatalogCardView:
        return CatalogCardView(
            catalog_item_id=item.catalog_item_id,
            display_name=item.name,
            article=item.article,
            sku=item.sku,
            supplier_code=item.supplier_code,
            product_type=item.product_type,
            category=item.category,
            brand=item.brand,
            manufacturer=item.manufacturer,
            availability_summary=self._availability_summary(item),
            price_summary=self._price_summary(item),
            highlights=self._highlights(item),
            status=item.status.value,
        )

    def _to_reference_row(self, item: CatalogItem) -> CatalogListRow:
        lowest_price = self._lowest_price(item)
        return CatalogListRow(
            catalog_item_id=item.catalog_item_id,
            article=item.article,
            internal_code=item.internal_code,
            supplier_code=item.supplier_code,
            name=item.name,
            product_type=item.product_type,
            category=item.category,
            group=item.group,
            subgroup=item.subgroup,
            brand=item.brand,
            manufacturer=item.manufacturer,
            unit=item.unit,
            available_quantity=decimal_to_json(self._available_quantity(item)) or "0",
            base_price=decimal_to_json(lowest_price.amount) if lowest_price else None,
            currency=lowest_price.currency if lowest_price else None,
            status=item.status.value,
            source=item.source.value if item.source else None,
            updated_at=item.updated_at.astimezone().isoformat(),
        )

    def _availability_summary(self, item: CatalogItem) -> dict[str, str | bool]:
        available = self._available_quantity(item)
        reserved = sum((balance.quantity_reserved for balance in self._stock_balances_for_item(item)), Decimal("0"))
        return {
            "has_stock": available > Decimal("0"),
            "available_quantity": decimal_to_json(available) or "0",
            "reserved_quantity": decimal_to_json(reserved) or "0",
            "unit": item.unit,
        }

    def _price_summary(self, item: CatalogItem) -> dict[str, str | bool | None]:
        lowest_price = self._lowest_price(item)
        return {
            "has_price": lowest_price is not None,
            "amount": decimal_to_json(lowest_price.amount) if lowest_price else None,
            "currency": lowest_price.currency if lowest_price else None,
            "price_type": lowest_price.price_type.value if lowest_price else None,
        }

    def _highlights(self, item: CatalogItem) -> dict[str, object]:
        priority_keys = ("measurement_range", "pressure_range", "temperature_range", "thread", "diameter", "material", "accuracy_class")
        return {key: item.attributes[key] for key in priority_keys if key in item.attributes}

    def _stock_balances_for_item(self, item: CatalogItem) -> tuple[StockBalance, ...]:
        return tuple(balance for balance in self._stock_balances.values() if balance.catalog_item_id == item.catalog_item_id)

    def _price_records_for_item(self, item: CatalogItem) -> tuple[PriceRecord, ...]:
        return tuple(record for record in self._price_records.values() if record.catalog_item_id == item.catalog_item_id)

    def _available_quantity(self, item: CatalogItem) -> Decimal:
        return sum((balance.quantity_available for balance in self._stock_balances_for_item(item)), Decimal("0"))

    def _has_stock(self, item: CatalogItem) -> bool:
        return self._available_quantity(item) > Decimal("0")

    def _lowest_price(self, item: CatalogItem) -> Optional[PriceRecord]:
        records = self._price_records_for_item(item)
        if not records:
            return None
        base_records = [record for record in records if record.price_type == PriceType.BASE]
        selected = base_records or list(records)
        return sorted(selected, key=lambda record: (record.amount, record.currency))[0]

    def _lowest_price_amount(self, item: CatalogItem) -> Optional[Decimal]:
        price = self._lowest_price(item)
        return price.amount if price else None

    def _availability_bucket(self, item: CatalogItem) -> str:
        if self._available_quantity(item) > Decimal("0"):
            return "in_stock"
        if any(balance.quantity_reserved > Decimal("0") for balance in self._stock_balances_for_item(item)):
            return "reserved"
        return "unavailable"


def _count_values(values: Iterable[Optional[str]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        if not value:
            continue
        result[str(value)] = result.get(str(value), 0) + 1
    return dict(sorted(result.items()))
