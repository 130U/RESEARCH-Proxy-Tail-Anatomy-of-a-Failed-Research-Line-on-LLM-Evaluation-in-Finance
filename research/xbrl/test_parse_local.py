from pathlib import Path
import unittest
from research.xbrl.parse_local import parse_document

FIXTURE = Path(__file__).with_name("synthetic_fixture.xml")


class OfflineParserTests(unittest.TestCase):
    def modify(self, old, new):
        return parse_document(FIXTURE.read_bytes().replace(old.encode(), new.encode()))

    def test_exact_scale_sign_period_and_rounding(self):
        result = parse_document(FIXTURE.read_bytes())
        self.assertEqual(len(result["facts"]), 3)
        values = {r["id"]: r for r in result["facts"]}
        from decimal import Decimal
        self.assertEqual(Decimal(values["revenue"]["value"]), Decimal(123400000))
        self.assertEqual(Decimal(values["cash_change"]["value"]), Decimal(-5200))
        self.assertEqual(values["ratio"]["declared_rounding_enclosure"], ["0.1245", "0.1255"])
        self.assertEqual(values["revenue"]["context"]["period"], {"start": "2024-01-01", "end": "2024-03-31"})
        self.assertIsNone(result["timestamp_certificate"])

    def test_unknown_transformation_abstains(self):
        result = parse_document(FIXTURE.read_bytes())
        self.assertEqual(result["rejections"], [{"id": "unsupported", "reason": "transformation_registry_not_implemented"}])
        self.assertEqual(result["status"], "partial")

    def test_unknown_unit_and_context_are_not_guessed(self):
        self.assertEqual(len(self.modify('unitRef="USD"', 'unitRef="MISSING"')["facts"]), 1)
        self.assertEqual(len(self.modify('contextRef="quarter"', 'contextRef="MISSING"')["facts"]), 1)

    def test_continuation_abstains(self):
        result = self.modify('id="ratio" name=', 'id="ratio" continuedAt="more" name=')
        self.assertTrue(any(r["id"] == "ratio" for r in result["rejections"]))

    def test_period_and_scale_domain(self):
        self.assertEqual(len(self.modify('2024-01-01', '2024-05-01')["facts"]), 1)
        self.assertTrue(any(r["id"] == "revenue" for r in self.modify('scale="6"', 'scale="200"')["rejections"]))

    def test_unknown_sign_and_lexical_negative(self):
        self.assertTrue(any(r["id"] == "cash_change" for r in self.modify('sign="-"', 'sign="+"')["rejections"]))
        self.assertTrue(any(r["id"] == "ratio" for r in self.modify('>0.125<', '>-0.125<')["rejections"]))

    def test_duplicate_id_and_entities_rejected(self):
        with self.assertRaises(ValueError):
            self.modify('id="pure"', 'id="USD"')
        with self.assertRaises(ValueError):
            parse_document(b'<!DOCTYPE html><html/>')

    def test_decimal_declaration_required(self):
        result = self.modify(' decimals="3"', '')
        self.assertTrue(any(r["id"] == "ratio" and r["reason"] == "missing_decimals" for r in result["rejections"]))


if __name__ == "__main__":
    unittest.main()
