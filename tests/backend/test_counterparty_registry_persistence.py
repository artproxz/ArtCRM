import json
import unittest
from dataclasses import FrozenInstanceError, replace

from backend.app.common import ErrorCode
from backend.app.counterparties import (
    Counterparty,
    CounterpartyContact,
    CounterpartySourceType,
    CounterpartyStatus,
    CounterpartyType,
    InMemoryCounterpartyRepository,
    build_contact_dedup_key,
    build_counterparty_dedup_key,
    merge_unique_values,
    normalize_email,
    normalize_inn,
    normalize_kpp,
    normalize_name,
    normalize_ogrn,
    normalize_phone,
    normalize_tag,
    normalize_website,
)


class CounterpartyRegistryPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryCounterpartyRepository()

    def test_counterparty_can_be_created_with_stable_id_and_ref(self):
        counterparty = Counterparty(counterparty_id="cp-001", display_name="Demo Company")

        result = self.repository.create_counterparty(counterparty)

        self.assertTrue(result.success)
        self.assertEqual(result.value.counterparty_id, "cp-001")
        self.assertEqual(result.value.ref, "counterparty:cp-001")

    def test_counterparty_defaults_are_sane(self):
        counterparty = Counterparty(counterparty_id="cp-001", display_name="  Demo Company  ")

        self.assertEqual(counterparty.display_name, "Demo Company")
        self.assertEqual(counterparty.status, CounterpartyStatus.ACTIVE)
        self.assertEqual(counterparty.counterparty_type, CounterpartyType.COMPANY)
        self.assertEqual(counterparty.emails, ())
        self.assertEqual(counterparty.phones, ())
        self.assertEqual(counterparty.websites, ())
        self.assertEqual(counterparty.contact_refs, ())
        self.assertEqual(counterparty.normalized_display_name, "demo company")

    def test_counterparty_contact_can_be_created_with_stable_id_and_ref(self):
        contact = CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Demo Person")

        self.assertEqual(contact.contact_id, "contact-001")
        self.assertEqual(contact.ref, "counterparty_contact:contact-001")
        self.assertEqual(contact.counterparty_id, "cp-001")

    def test_contact_can_be_added_to_existing_counterparty(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        contact = CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Demo Person")

        result = self.repository.create_contact(contact)

        self.assertTrue(result.success)
        self.assertEqual(result.value.ref, "counterparty_contact:contact-001")

    def test_contact_cannot_be_added_to_unknown_counterparty(self):
        contact = CounterpartyContact(contact_id="contact-001", counterparty_id="missing", full_name="Demo Person")

        result = self.repository.create_contact(contact)
        missing_contact = self.repository.get_contact("contact-001")

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.NOT_FOUND)
        self.assertEqual(result.error.entity_ref, "counterparty:missing")
        self.assertFalse(missing_contact.success)
        self.assertEqual(missing_contact.error.code, ErrorCode.NOT_FOUND)

    def test_repository_can_get_counterparty_by_id(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))

        result = self.repository.get_counterparty("cp-001")

        self.assertTrue(result.success)
        self.assertEqual(result.value.display_name, "Demo Company")

    def test_repository_can_list_counterparties(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="One"))
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-002", display_name="Two"))

        counterparties = self.repository.list_counterparties()

        self.assertEqual(len(counterparties), 2)
        self.assertEqual({counterparty.counterparty_id for counterparty in counterparties}, {"cp-001", "cp-002"})

    def test_repository_can_get_contact_by_id(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        self.repository.create_contact(
            CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Demo Person")
        )

        result = self.repository.get_contact("contact-001")

        self.assertTrue(result.success)
        self.assertEqual(result.value.full_name, "Demo Person")

    def test_repository_can_list_contacts_by_counterparty(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        self.repository.create_contact(
            CounterpartyContact(contact_id="contact-002", counterparty_id="cp-001", full_name="Second")
        )
        self.repository.create_contact(
            CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="First")
        )

        result = self.repository.list_contacts_by_counterparty("cp-001")

        self.assertTrue(result.success)
        self.assertEqual({contact.contact_id for contact in result.value}, {"contact-001", "contact-002"})

    def test_duplicate_counterparty_id_is_rejected(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))

        result = self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Other"))

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.CONFLICT)

    def test_duplicate_contact_id_is_rejected(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        self.repository.create_contact(
            CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="One")
        )

        result = self.repository.create_contact(
            CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Two")
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.CONFLICT)

    def test_creating_contact_updates_counterparty_contact_refs(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        self.repository.create_contact(
            CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Demo Person")
        )

        counterparty = self.repository.get_counterparty("cp-001").value

        self.assertEqual(counterparty.contact_refs, ("counterparty_contact:contact-001",))

    def test_set_primary_contact_marks_selected_contact_primary_and_others_non_primary(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        self.repository.create_contact(
            CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="One", is_primary=True)
        )
        self.repository.create_contact(
            CounterpartyContact(contact_id="contact-002", counterparty_id="cp-001", full_name="Two")
        )

        result = self.repository.set_primary_contact("cp-001", "contact-002")

        self.assertTrue(result.success)
        self.assertFalse(self.repository.get_contact("contact-001").value.is_primary)
        self.assertTrue(self.repository.get_contact("contact-002").value.is_primary)

    def test_update_counterparty_updates_non_sensitive_fields(self):
        original = Counterparty(counterparty_id="cp-001", display_name="Demo Company", industry="KIP")
        self.repository.create_counterparty(original)
        updated = replace(original, display_name="Updated Company", industry="Instrumentation")

        result = self.repository.update_counterparty(updated)

        self.assertTrue(result.success)
        self.assertEqual(result.value.display_name, "Updated Company")
        self.assertEqual(result.value.industry, "Instrumentation")
        self.assertEqual(result.value.status, CounterpartyStatus.ACTIVE)

    def test_update_counterparty_rejects_direct_status_change(self):
        original = Counterparty(counterparty_id="cp-001", display_name="Demo Company")
        self.repository.create_counterparty(original)
        changed = replace(original, status=CounterpartyStatus.ARCHIVED, display_name="Updated")

        result = self.repository.update_counterparty(changed)

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.INVALID_STATE_TRANSITION)
        self.assertEqual(self.repository.get_counterparty("cp-001").value.status, CounterpartyStatus.ACTIVE)

    def test_update_contact_updates_non_sensitive_fields(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        original = CounterpartyContact(
            contact_id="contact-001",
            counterparty_id="cp-001",
            full_name="Demo Person",
            position_title="Manager",
        )
        self.repository.create_contact(original)
        updated = replace(original, position_title="Director", notes="Updated note")

        result = self.repository.update_contact(updated)

        self.assertTrue(result.success)
        self.assertEqual(result.value.position_title, "Director")
        self.assertEqual(result.value.notes, "Updated note")

    def test_update_contact_rejects_direct_primary_change(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        original = CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Demo Person")
        self.repository.create_contact(original)
        changed = replace(original, is_primary=True)

        result = self.repository.update_contact(changed)

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.CONFLICT)
        self.assertFalse(self.repository.get_contact("contact-001").value.is_primary)

    def test_update_contact_rejects_direct_counterparty_id_change(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-002", display_name="Other Company"))
        original = CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Demo Person")
        self.repository.create_contact(original)
        changed = replace(original, counterparty_id="cp-002", full_name="Moved Person")

        result = self.repository.update_contact(changed)

        stored = self.repository.get_contact("contact-001").value
        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.CONFLICT)
        self.assertEqual(stored.counterparty_id, "cp-001")
        self.assertEqual(stored.full_name, "Demo Person")

    def test_archive_counterparty_changes_status_safely(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))

        result = self.repository.archive_counterparty("cp-001")

        self.assertTrue(result.success)
        self.assertEqual(result.value.status, CounterpartyStatus.ARCHIVED)
        self.assertEqual(self.repository.get_counterparty("cp-001").value.status, CounterpartyStatus.ARCHIVED)

    def test_normalize_inn_removes_non_digits(self):
        self.assertEqual(normalize_inn(" INN 7707-123 456 "), "7707123456")

    def test_normalize_kpp_removes_non_digits(self):
        self.assertEqual(normalize_kpp(" KPP 7707-01-001 "), "770701001")

    def test_normalize_ogrn_removes_non_digits(self):
        self.assertEqual(normalize_ogrn(" OGRN 102-7700-123456 "), "1027700123456")

    def test_normalize_email_lowercases_and_trims(self):
        self.assertEqual(normalize_email("  Sales@Example.COM  "), "sales@example.com")

    def test_normalize_phone_returns_stable_normalized_value(self):
        self.assertEqual(normalize_phone(" +7 (343) 222-33-44 "), "+73432223344")
        self.assertEqual(normalize_phone("8 (343) 222-33-44"), "83432223344")

    def test_normalize_website_trims_lowercases_and_removes_trailing_slash(self):
        self.assertEqual(normalize_website(" HTTPS://Example.COM/ "), "example.com")
        self.assertEqual(normalize_website("Example.COM/path/"), "example.com/path")

    def test_normalize_name_trims_lowercases_and_collapses_spaces(self):
        self.assertEqual(normalize_name("  Demo    Company  "), "demo company")

    def test_normalize_tag_trims_lowercases_and_collapses_spaces(self):
        self.assertEqual(normalize_tag("  VIP    Customer  "), "vip customer")

    def test_merge_unique_values_removes_blanks_and_duplicates_preserving_order(self):
        result = merge_unique_values("sales@example.com", ["", "INFO@example.com", "sales@example.com", "info@example.com"])

        self.assertEqual(result, ("sales@example.com", "INFO@example.com"))

    def test_build_counterparty_dedup_key_prefers_inn(self):
        counterparty = Counterparty(
            counterparty_id="cp-001",
            display_name="Demo Company",
            inn="77 07 123456",
            primary_email="sales@example.com",
        )

        self.assertEqual(build_counterparty_dedup_key(counterparty), "counterparty:inn:7707123456")

    def test_build_counterparty_dedup_key_falls_back_to_name_and_email(self):
        counterparty = Counterparty(
            counterparty_id="cp-001",
            display_name="Demo Company",
            primary_email="Sales@Example.com",
        )

        self.assertEqual(build_counterparty_dedup_key(counterparty), "counterparty:fallback:demo company:sales@example.com")

    def test_build_counterparty_dedup_key_falls_back_to_name_and_phone_or_site(self):
        phone_counterparty = Counterparty(
            counterparty_id="cp-001",
            display_name="Demo Company",
            primary_phone="+7 (343) 222-33-44",
        )
        site_counterparty = Counterparty(
            counterparty_id="cp-002",
            display_name="Demo Company",
            primary_website="Example.com/",
        )

        self.assertEqual(build_counterparty_dedup_key(phone_counterparty), "counterparty:fallback:demo company:+73432223344")
        self.assertEqual(build_counterparty_dedup_key(site_counterparty), "counterparty:fallback:demo company:example.com")

    def test_build_contact_dedup_key_prefers_counterparty_and_email(self):
        contact = CounterpartyContact(
            contact_id="contact-001",
            counterparty_id="cp-001",
            full_name="Demo Person",
            primary_email="Person@Example.com",
            primary_phone="+7 343 222-33-44",
        )

        self.assertEqual(build_contact_dedup_key(contact), "contact:cp-001:email:person@example.com")

    def test_build_contact_dedup_key_falls_back_to_counterparty_and_phone(self):
        contact = CounterpartyContact(
            contact_id="contact-001",
            counterparty_id="cp-001",
            full_name="Demo Person",
            primary_phone="+7 343 222-33-44",
        )

        self.assertEqual(build_contact_dedup_key(contact), "contact:cp-001:phone:+73432223344")

    def test_build_contact_dedup_key_falls_back_to_counterparty_and_normalized_name(self):
        contact = CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="  Demo   Person ")

        self.assertEqual(build_contact_dedup_key(contact), "contact:cp-001:name:demo person")

    def test_find_counterparty_by_dedup_key(self):
        counterparty = Counterparty(counterparty_id="cp-001", display_name="Demo Company", inn="7707123456")
        self.repository.create_counterparty(counterparty)

        result = self.repository.find_counterparty_by_dedup_key("counterparty:inn:7707123456")

        self.assertTrue(result.success)
        self.assertEqual(result.value.counterparty_id, "cp-001")

    def test_find_contact_by_dedup_key(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        contact = CounterpartyContact(
            contact_id="contact-001",
            counterparty_id="cp-001",
            full_name="Demo Person",
            primary_email="person@example.com",
        )
        self.repository.create_contact(contact)

        result = self.repository.find_contact_by_dedup_key("contact:cp-001:email:person@example.com")

        self.assertTrue(result.success)
        self.assertEqual(result.value.contact_id, "contact-001")

    def test_public_counterparty_serialization_hides_internal_notes_external_refs_and_responsible_user(self):
        counterparty = Counterparty(
            counterparty_id="cp-001",
            display_name="Demo Company",
            internal_notes="Internal note",
            external_refs={"amocrm_id": "123"},
            responsible_user_ref="user:manager",
            source=CounterpartySourceType.AMOCRM,
        )

        payload = counterparty.to_public_dict()

        self.assertNotIn("internal_notes", payload)
        self.assertNotIn("external_refs", payload)
        self.assertNotIn("responsible_user_ref", payload)
        self.assertNotIn("source", payload)

    def test_internal_counterparty_serialization_includes_internal_fields(self):
        counterparty = Counterparty(
            counterparty_id="cp-001",
            display_name="Demo Company",
            internal_notes="Internal note",
            external_refs={"amocrm_id": "123"},
            responsible_user_ref="user:manager",
            source=CounterpartySourceType.AMOCRM,
            tags=("VIP",),
        )

        payload = counterparty.to_dict()

        self.assertEqual(payload["internal_notes"], "Internal note")
        self.assertEqual(payload["external_refs"], {"amocrm_id": "123"})
        self.assertEqual(payload["responsible_user_ref"], "user:manager")
        self.assertEqual(payload["source"], "amocrm")
        self.assertEqual(payload["tags"], ["vip"])

    def test_public_contact_serialization_hides_internal_notes_external_refs_and_source(self):
        contact = CounterpartyContact(
            contact_id="contact-001",
            counterparty_id="cp-001",
            full_name="Demo Person",
            internal_notes="Internal note",
            external_refs={"amocrm_contact_id": "123"},
            source=CounterpartySourceType.AMOCRM,
        )

        payload = contact.to_public_dict()

        self.assertNotIn("internal_notes", payload)
        self.assertNotIn("external_refs", payload)
        self.assertNotIn("source", payload)

    def test_internal_contact_serialization_includes_internal_fields(self):
        contact = CounterpartyContact(
            contact_id="contact-001",
            counterparty_id="cp-001",
            full_name="Demo Person",
            internal_notes="Internal note",
            external_refs={"amocrm_contact_id": "123"},
            source=CounterpartySourceType.AMOCRM,
        )

        payload = contact.to_dict()

        self.assertEqual(payload["internal_notes"], "Internal note")
        self.assertEqual(payload["external_refs"], {"amocrm_contact_id": "123"})
        self.assertEqual(payload["source"], "amocrm")

    def test_serialization_returns_json_friendly_plain_dicts(self):
        counterparty = Counterparty(
            counterparty_id="cp-001",
            display_name="Demo Company",
            emails=("Sales@Example.com",),
            phones=("+7 343 222-33-44",),
            websites=("Example.com/",),
            external_refs={"amocrm_id": "123"},
        )
        contact = CounterpartyContact(
            contact_id="contact-001",
            counterparty_id="cp-001",
            full_name="Demo Person",
            emails=("Person@Example.com",),
            external_refs={"amocrm_contact_id": "456"},
        )

        counterparty_payload = counterparty.to_dict()
        contact_payload = contact.to_dict()

        self.assertIsInstance(counterparty_payload, dict)
        self.assertIsInstance(contact_payload, dict)
        self.assertIsInstance(counterparty_payload["emails"], list)
        self.assertIsInstance(counterparty_payload["external_refs"], dict)
        self.assertIsInstance(contact_payload["emails"], list)
        self.assertIsInstance(contact_payload["external_refs"], dict)
        json.dumps(counterparty_payload)
        json.dumps(contact_payload)

    def test_json_dumps_counterparty_public_dict_works(self):
        counterparty = Counterparty(counterparty_id="cp-001", display_name="Demo Company", internal_notes="Internal")

        encoded = json.dumps(counterparty.to_public_dict())

        self.assertIn('"display_name": "Demo Company"', encoded)
        self.assertNotIn("Internal", encoded)

    def test_json_dumps_contact_public_dict_works(self):
        contact = CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Demo Person")

        encoded = json.dumps(contact.to_public_dict())

        self.assertIn('"full_name": "Demo Person"', encoded)

    def test_repository_returns_immutable_safe_objects(self):
        self.repository.create_counterparty(Counterparty(counterparty_id="cp-001", display_name="Demo Company"))
        self.repository.create_contact(
            CounterpartyContact(contact_id="contact-001", counterparty_id="cp-001", full_name="Demo Person")
        )

        counterparty = self.repository.get_counterparty("cp-001").value
        contact = self.repository.get_contact("contact-001").value

        with self.assertRaises(FrozenInstanceError):
            counterparty.display_name = "Mutated"
        with self.assertRaises(FrozenInstanceError):
            contact.full_name = "Mutated"
        with self.assertRaises(TypeError):
            counterparty.external_refs["amocrm_id"] = "123"

    def test_repository_test_store_is_isolated_between_tests(self):
        self.assertEqual(self.repository.list_counterparties(), ())

    def test_missing_counterparty_returns_safe_not_found(self):
        result = self.repository.get_counterparty("missing")

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.NOT_FOUND)

    def test_missing_contact_returns_safe_not_found(self):
        result = self.repository.get_contact("missing")

        self.assertFalse(result.success)
        self.assertEqual(result.error.code, ErrorCode.NOT_FOUND)

    def test_model_uses_canonical_fields_for_future_csv_duplicate_aliases(self):
        counterparty = Counterparty(
            counterparty_id="cp-001",
            display_name="Demo Company",
            industry="Instrumentation",
            primary_website="Example.com",
            websites=("Web2.example.com",),
            primary_email="info@example.com",
            emails=("sales@example.com",),
            primary_phone="+7 343 222-33-44",
            phones=("8 343 222-33-45",),
        )

        payload = counterparty.to_dict()

        self.assertEqual(payload["industry"], "Instrumentation")
        self.assertEqual(payload["primary_website"], "example.com")
        self.assertEqual(payload["websites"], ["example.com", "web2.example.com"])
        self.assertEqual(payload["primary_email"], "info@example.com")
        self.assertEqual(payload["emails"], ["info@example.com", "sales@example.com"])
        self.assertEqual(payload["primary_phone"], "+73432223344")
        self.assertEqual(payload["phones"], ["+73432223344", "83432223345"])
        for duplicate_field in ("sphere", "activity", "site_company", "site", "web2", "email_company", "official_email"):
            self.assertNotIn(duplicate_field, payload)


if __name__ == "__main__":
    unittest.main()
