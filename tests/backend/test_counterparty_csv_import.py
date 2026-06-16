import csv
import json
import unittest
from io import StringIO

from backend.app.counterparties import Counterparty, CounterpartyContact, InMemoryCounterpartyRepository
from backend.app.counterparties.importing import (
    ROW_STATUS_CREATE,
    ROW_STATUS_SKIPPED,
    ROW_STATUS_UPDATE,
    apply_counterparty_csv_import,
    map_counterparty_csv_row,
    parse_counterparty_csv_text,
    preview_counterparty_csv_import,
)


class CounterpartyCsvImportTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryCounterpartyRepository()

    def test_parser_reads_csv_text_with_russian_headers(self):
        rows = parse_counterparty_csv_text(_csv({"Название компании": "ООО Ромашка", "ИНН компании": "7707123456"}))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Название компании"], "ООО Ромашка")
        self.assertEqual(rows[0]["ИНН компании"], "7707123456")

    def test_empty_csv_returns_empty_preview_safely(self):
        preview = preview_counterparty_csv_import("", self.repository)

        self.assertEqual(preview.summary.rows_total, 0)
        self.assertEqual(preview.rows, ())

    def test_missing_company_identity_row_is_skipped_safely(self):
        preview = preview_counterparty_csv_import(_csv({"Контактное лицо": "Иван Иванов"}), self.repository)

        self.assertEqual(preview.summary.rows_total, 1)
        self.assertEqual(preview.summary.counterparties_skipped, 1)
        self.assertEqual(preview.summary.errors, 1)
        self.assertEqual(preview.rows[0].status, ROW_STATUS_SKIPPED)
        self.assertIn("missing_company_identity", preview.rows[0].errors)

    def test_company_name_maps_to_display_name(self):
        mapped = map_counterparty_csv_row({"Название компании": "ООО Ромашка"}, 2)

        self.assertEqual(mapped.counterparty.display_name, "ООО Ромашка")

    def test_legal_name_maps_to_legal_name(self):
        mapped = map_counterparty_csv_row(
            {
                "Название компании": "Ромашка",
                "Полное юридическое наименование": "Общество с ограниченной ответственностью Ромашка",
            },
            2,
        )

        self.assertEqual(mapped.counterparty.legal_name, "Общество с ограниченной ответственностью Ромашка")

    def test_inn_kpp_and_ogrn_are_normalized(self):
        mapped = map_counterparty_csv_row(
            {
                "Название компании": "Ромашка",
                "ИНН компании": "77 07-123456",
                "КПП": "7707-01-001",
                "ОГРН": "102-7700-123456",
            },
            2,
        )

        self.assertEqual(mapped.counterparty.inn, "7707123456")
        self.assertEqual(mapped.counterparty.kpp, "770701001")
        self.assertEqual(mapped.counterparty.ogrn, "1027700123456")

    def test_industry_aliases_map_to_canonical_industry_with_precedence(self):
        row = {"Название компании": "Ромашка", "Сфера деятельности": "КИП", "Сфера": "Производство"}

        mapped = map_counterparty_csv_row(row, 2)

        self.assertEqual(mapped.counterparty.industry, "КИП")

    def test_short_industry_alias_maps_when_primary_alias_absent(self):
        row = {"Название компании": "Ромашка", "Сфера": "Производство"}

        mapped = map_counterparty_csv_row(row, 2)

        self.assertEqual(mapped.counterparty.industry, "Производство")

    def test_website_aliases_map_to_primary_website_and_websites(self):
        row = {
            "Название компании": "Ромашка",
            "Cайт компании": "https://Example.com/",
            "Сайт": "example.ru",
            "Web2": "web2.example.org",
        }

        mapped = map_counterparty_csv_row(row, 2)

        self.assertEqual(mapped.counterparty.primary_website, "example.com")
        self.assertEqual(mapped.counterparty.websites, ("example.com", "example.ru", "web2.example.org"))

    def test_email_aliases_map_to_primary_email_and_emails(self):
        row = {
            "Название компании": "Ромашка",
            "Email компании": "Info@Example.com",
            "Официальная почта": "Sales@Example.com",
        }

        mapped = map_counterparty_csv_row(row, 2)

        self.assertEqual(mapped.counterparty.primary_email, "info@example.com")
        self.assertEqual(mapped.counterparty.emails, ("info@example.com", "sales@example.com"))

    def test_phone_aliases_map_to_primary_phone_and_phones(self):
        row = {
            "Название компании": "Ромашка",
            "Телефон компании": "+7 (343) 222-33-44",
            "Дополнительный телефон": "8 (343) 222-33-45",
        }

        mapped = map_counterparty_csv_row(row, 2)

        self.assertEqual(mapped.counterparty.primary_phone, "+73432223344")
        self.assertEqual(mapped.counterparty.phones, ("+73432223344", "83432223345"))

    def test_contact_columns_create_counterparty_contact_draft(self):
        mapped = map_counterparty_csv_row(
            {
                "Название компании": "Ромашка",
                "Контактное лицо": "Иван Иванов",
                "Должность": "Инженер",
                "Почта контактного лица": "Ivan@Example.com",
                "Телефон контактного лица": "+7 (900) 111-22-33",
            },
            2,
        )

        self.assertIsNotNone(mapped.contact)
        self.assertEqual(mapped.contact.full_name, "Иван Иванов")
        self.assertEqual(mapped.contact.position_title, "Инженер")
        self.assertEqual(mapped.contact.primary_email, "ivan@example.com")
        self.assertEqual(mapped.contact.primary_phone, "+79001112233")

    def test_contact_is_not_created_when_contact_fields_are_empty(self):
        mapped = map_counterparty_csv_row({"Название компании": "Ромашка"}, 2)

        self.assertIsNone(mapped.contact)

    def test_preview_does_not_mutate_repository(self):
        preview = preview_counterparty_csv_import(_csv(_full_row()), self.repository)

        self.assertEqual(preview.rows[0].status, ROW_STATUS_CREATE)
        self.assertEqual(self.repository.list_counterparties(), ())

    def test_apply_creates_counterparty(self):
        result = apply_counterparty_csv_import(_csv(_full_row()), self.repository)

        counterparties = self.repository.list_counterparties()
        self.assertEqual(result.summary.counterparties_created, 1)
        self.assertEqual(len(counterparties), 1)
        self.assertEqual(counterparties[0].display_name, "ООО Ромашка")

    def test_apply_creates_linked_contact(self):
        apply_counterparty_csv_import(_csv(_full_row()), self.repository)
        counterparty = self.repository.list_counterparties()[0]
        contacts = self.repository.list_contacts_by_counterparty(counterparty.counterparty_id).value

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].full_name, "Иван Иванов")
        self.assertEqual(counterparty.contact_refs, ("counterparty_contact:imported-contact-000001",))

    def test_apply_does_not_create_orphan_contact_for_skipped_row(self):
        result = apply_counterparty_csv_import(_csv({"Контактное лицо": "Иван Иванов"}), self.repository)

        self.assertEqual(result.summary.counterparties_skipped, 1)
        self.assertEqual(self.repository.list_counterparties(), ())
        self.assertFalse(self.repository.get_contact("imported-contact-000001").success)

    def test_same_inn_dedups_counterparty(self):
        csv_text = _csv_many(
            [
                {"Название компании": "Ромашка 1", "ИНН компании": "7707123456"},
                {"Название компании": "Ромашка 2", "ИНН компании": "77 07 123456"},
            ]
        )

        result = apply_counterparty_csv_import(csv_text, self.repository)

        self.assertEqual(len(self.repository.list_counterparties()), 1)
        self.assertEqual(result.summary.counterparties_created, 1)
        self.assertEqual(result.summary.counterparties_updated, 1)
        self.assertGreaterEqual(result.summary.duplicates, 1)

    def test_existing_counterparty_is_updated_by_dedup_key(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-existing", display_name="Old", inn="7707123456"))
        csv_text = _csv({"Название компании": "New", "ИНН компании": "7707123456", "Сфера": "КИП"})

        result = apply_counterparty_csv_import(csv_text, self.repository)

        counterparty = self.repository.get_counterparty("cp-existing").value
        self.assertEqual(result.rows[0].status, ROW_STATUS_UPDATE)
        self.assertEqual(counterparty.counterparty_id, "cp-existing")
        self.assertEqual(counterparty.display_name, "New")
        self.assertEqual(counterparty.industry, "КИП")

    def test_same_counterparty_and_contact_email_dedups_contact(self):
        result = apply_counterparty_csv_import(
            _csv_many(
                [
                    {
                        "Название компании": "Ромашка",
                        "ИНН компании": "7707123456",
                        "Контактное лицо": "Иван",
                        "Почта контактного лица": "ivan@example.com",
                    },
                    {
                        "Название компании": "Ромашка",
                        "ИНН компании": "7707123456",
                        "Контактное лицо": "Иван Петров",
                        "Почта контактного лица": "Ivan@Example.com",
                    },
                ]
            ),
            self.repository,
        )

        counterparty = self.repository.list_counterparties()[0]
        contacts = self.repository.list_contacts_by_counterparty(counterparty.counterparty_id).value
        self.assertEqual(len(contacts), 1)
        self.assertEqual(result.summary.contacts_created, 1)
        self.assertEqual(result.summary.contacts_updated, 1)

    def test_same_counterparty_and_contact_phone_dedups_contact(self):
        result = apply_counterparty_csv_import(
            _csv_many(
                [
                    {
                        "Название компании": "Ромашка",
                        "ИНН компании": "7707123456",
                        "Контактное лицо": "Иван",
                        "Телефон контактного лица": "+7 (900) 111-22-33",
                    },
                    {
                        "Название компании": "Ромашка",
                        "ИНН компании": "7707123456",
                        "Контактное лицо": "Иван Петров",
                        "Телефон контактного лица": "+7 900 111 22 33",
                    },
                ]
            ),
            self.repository,
        )

        counterparty = self.repository.list_counterparties()[0]
        contacts = self.repository.list_contacts_by_counterparty(counterparty.counterparty_id).value
        self.assertEqual(len(contacts), 1)
        self.assertEqual(result.summary.contacts_updated, 1)

    def test_same_counterparty_and_contact_name_dedups_contact_fallback(self):
        result = apply_counterparty_csv_import(
            _csv_many(
                [
                    {"Название компании": "Ромашка", "ИНН компании": "7707123456", "Контактное лицо": "Иван Иванов"},
                    {"Название компании": "Ромашка", "ИНН компании": "7707123456", "Контактное лицо": "  Иван   Иванов "},
                ]
            ),
            self.repository,
        )

        counterparty = self.repository.list_counterparties()[0]
        contacts = self.repository.list_contacts_by_counterparty(counterparty.counterparty_id).value
        self.assertEqual(len(contacts), 1)
        self.assertEqual(result.summary.contacts_updated, 1)

    def test_amocrm_id_maps_to_external_refs(self):
        mapped = map_counterparty_csv_row({"Название компании": "Ромашка", "amoCRM ID": "12345"}, 2)

        self.assertEqual(dict(mapped.counterparty.external_refs), {"amocrm_id": "12345"})

    def test_amocrm_tags_map_to_tags(self):
        mapped = map_counterparty_csv_row({"Название компании": "Ромашка", "Теги amoCRM": "vip; завод"}, 2)

        self.assertEqual(mapped.counterparty.tags, ("vip", "завод"))

    def test_note_maps_to_notes_and_metadata_does_not_create_duplicate_fields(self):
        mapped = map_counterparty_csv_row(
            {
                "Название компании": "Ромашка",
                "Примечание": "Комментарий",
                "Сделки amoCRM": "deal-1",
                "ДОГОВОР / УСЛ.-Я": "contract-1",
            },
            2,
        )

        payload = mapped.counterparty.to_dict()
        self.assertIn("Комментарий", payload["notes"])
        self.assertIn("amocrm_deals: deal-1", payload["notes"])
        self.assertIn("contract_terms: contract-1", payload["notes"])
        self.assertNotIn("Сделки amoCRM", payload)
        self.assertNotIn("ДОГОВОР / УСЛ.-Я", payload)

    def test_annual_turnover_remains_string(self):
        mapped = map_counterparty_csv_row({"Название компании": "Ромашка", "ОБОРОТ за год": "7 млн руб."}, 2)

        self.assertEqual(mapped.counterparty.annual_turnover, "7 млн руб.")

    def test_disallowed_duplicate_backend_fields_are_not_in_payload(self):
        preview = preview_counterparty_csv_import(_csv(_full_row()), self.repository)
        payload = preview.rows[0].counterparty_preview

        for field in (
            "sphere",
            "activity",
            "site_company",
            "site",
            "web2",
            "email_company",
            "official_email",
            "phone_company",
            "additional_phone",
        ):
            self.assertNotIn(field, payload)

    def test_preview_result_is_json_friendly(self):
        preview = preview_counterparty_csv_import(_csv(_full_row()), self.repository)

        encoded = json.dumps(preview.to_dict(), ensure_ascii=False)

        self.assertIn("ООО Ромашка", encoded)

    def test_apply_result_is_json_friendly(self):
        result = apply_counterparty_csv_import(_csv(_full_row()), self.repository)

        encoded = json.dumps(result.to_dict(), ensure_ascii=False)

        self.assertIn("ООО Ромашка", encoded)

    def test_summary_counts_include_row_statuses(self):
        result = apply_counterparty_csv_import(_csv_many([_full_row(), {"Контактное лицо": "Без компании"}]), self.repository)

        self.assertEqual(result.summary.rows_total, 2)
        self.assertEqual(result.summary.counterparties_created, 1)
        self.assertEqual(result.summary.counterparties_skipped, 1)
        self.assertEqual(result.summary.contacts_created, 1)
        self.assertEqual(result.summary.errors, 1)
        self.assertEqual({row.status for row in result.rows}, {ROW_STATUS_CREATE, ROW_STATUS_SKIPPED})


def _full_row():
    return {
        "Название компании": "ООО Ромашка",
        "Полное юридическое наименование": "Общество с ограниченной ответственностью Ромашка",
        "ИНН компании": "7707123456",
        "КПП": "770701001",
        "ОГРН": "1027700123456",
        "Ответственный": "Demo Manager",
        "Тип заявки": "demo request",
        "Категория": "A",
        "Сфера деятельности": "КИП",
        "Сфера": "Производство",
        "ОБОРОТ за год": "7 млн руб.",
        "Источник": "amocrm",
        "Уровень клиента": "VIP",
        "Телефон компании": "+7 (343) 222-33-44",
        "Дополнительный телефон": "8 (343) 222-33-45",
        "Email компании": "info@example.com",
        "Официальная почта": "sales@example.com",
        "Cайт компании": "https://example.com",
        "Сайт": "example.ru",
        "Web2": "web2.example.org",
        "Фактический адрес компании": "Екатеринбург",
        "Юридический адрес компании": "Москва",
        "Примечание": "Комментарий",
        "amoCRM ID": "12345",
        "Теги amoCRM": "vip;завод",
        "Сделки amoCRM": "deal-1",
        "ДОГОВОР / УСЛ.-Я": "contract-1",
        "Контактное лицо": "Иван Иванов",
        "Должность": "Инженер",
        "Почта контактного лица": "ivan@example.com",
        "Телефон контактного лица": "+7 (900) 111-22-33",
    }


def _csv(row):
    return _csv_many([row])


def _csv_many(rows):
    headers = []
    for row in rows:
        for key in row:
            if key not in headers:
                headers.append(key)
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
