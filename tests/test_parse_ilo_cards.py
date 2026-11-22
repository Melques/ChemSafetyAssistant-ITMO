"""Regression checks against the actual saved ILO cards; no generated chemical facts."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.parse_ilo_cards import FIELDNAMES, build_csv, parse_card

ROOT = Path(__file__).resolve().parents[1]
ILO = ROOT / "data/raw/sds/ILO"


class TestILOParser(unittest.TestCase):
    def card(self, number: str) -> dict[str, str]:
        return parse_card(ILO / f"{number}.html", ILO)

    def test_identity_and_actual_language_not_html_wrapper(self):
        row = self.card("0001")
        self.assertEqual(row["name"], "ВОДОРОД")
        self.assertEqual(row["icsc_number"], "0001")
        self.assertEqual(row["cas"], "1333-74-0")
        self.assertEqual(row["un_number"], "1049")
        self.assertEqual(row["einecs"], "215-605-7")
        self.assertEqual(row["lang"], "ru")  # The actual HTML wrapper says lang="en".
        self.assertEqual(row["doc_id"], "ilo_icsc_0001_ru_v2")
        self.assertEqual(row["source"], "0001.html")

    def test_route_rows_do_not_shift_or_merge(self):
        row = self.card("0001")
        self.assertEqual(row["inhalation_symptoms"], "Головокружение. Головная боль. Вялость. Удушье.")
        self.assertEqual(row["inhalation_prevention"], "Применять вентиляцию.")
        self.assertEqual(row["inhalation_first_aid"], "Свежий воздух, покой.")
        self.assertEqual(row["skin_contact_symptoms"], "ПРИ КОНТАКТЕ С ГАЗОМ: ОБМОРОЖЕНИЕ.")
        self.assertEqual(row["skin_contact_prevention"], "Перчатки для защиты от холода.")
        self.assertEqual(row["eye_contact_prevention"], "Использовать маску для лица.")
        self.assertIn("НЕ удалять одежду", row["skin_contact_first_aid"])
        self.assertNotIn("НЕ удалять одежду", row["eye_contact_first_aid"])
        self.assertEqual(row["ingestion_first_aid"], "")

    def test_empty_source_values_stay_empty(self):
        row = self.card("0001")
        for column in (
            "packaging", "ingestion_symptoms", "ingestion_prevention", "ingestion_first_aid",
            "occupational_exposure_limits", "environment", "effects_of_long_term_or_repeated_exposure",
        ):
            with self.subTest(column=column):
                self.assertEqual(row[column], "")
        self.assertEqual(self.card("0087")["eu_classification"], "")

    def test_temperature_and_units_are_not_relabelled_or_converted(self):
        self.assertEqual(self.card("0001")["vapour_pressure"], "Давление пара, kPa при 25°C: 165320")
        self.assertEqual(self.card("0087")["vapour_pressure"], "Давление пара, kPa при 20°C: 24")
        self.assertEqual(self.card("0012")["vapour_pressure"], "Давление пара, Pa при 574°C: 130")
        self.assertEqual(
            self.card("0001")["solubility_in_water"],
            "Растворимость в воде, мг/л при 21°C: 1.62 (очень слабая)",
        )
        self.assertEqual(self.card("0087")["solubility_in_water"], "Растворимость в воде: смешивается")

    def test_formula_subscripts_and_signs_survive(self):
        self.assertEqual(self.card("0001")["formula"], "H2")
        row = self.card("0087")
        self.assertEqual(row["formula"], "C3H6O / CH3-CO-CH3")
        self.assertEqual(row["melting_point"], "-95°C")
        self.assertEqual(row["flash_point"], "-18°C c.c.")

    def test_rowspan_sections_and_transport_are_separate(self):
        row = self.card("0001")
        self.assertTrue(row["spillage_disposal"].startswith("Покинуть опасную зону!"))
        self.assertTrue(row["storage"].startswith("Обеспечить огнестойкость."))
        self.assertEqual(row["un_classification"], "Класс опасности по ООН: 2.1")
        self.assertNotIn("Класс опасности по ООН", row["classification_and_labelling"])
        self.assertNotIn("КЛАССИФИКАЦИЯ", row["spillage_disposal"])
        self.assertIn("flam;flame", row["classification_and_labelling"])

    def test_eu_label_after_inline_preface(self):
        self.assertEqual(
            self.card("0610")["eu_classification"],
            "Символ: T, N; R: 45-22-51/53; S: 53-45-61; Примечание: E",
        )

    def test_autoignition_qualifier_is_not_lost(self):
        self.assertEqual(
            self.card("0020")["auto_ignition_temperature"],
            "Металлической пыли кадмияТемпература самовоспламенения : 250°C",
        )
        self.assertEqual(
            self.card("0497")["auto_ignition_temperature"],
            "ПредположительноТемпература самовоспламенения : 277°C",
        )

    def test_property_pressure_qualifier_and_note_survive(self):
        self.assertEqual(self.card("0757")["boiling_point"], "при 2.6kPa: 129°C\nСм. Примечания.")
        self.assertEqual(self.card("1488")["auto_ignition_temperature"], "330-410°C\nСм. Примечания.")

    def test_no_translation_of_mixed_language_source(self):
        self.assertIn(
            "Measure hydrogen concentrations with suitable gas detector",
            self.card("0001")["notes"],
        )

    def test_csv_roundtrip_and_deterministic_single_file(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            raw = base / "raw"
            raw.mkdir()
            for number in ("0087", "0001"):
                (raw / f"{number}.html").write_bytes((ILO / f"{number}.html").read_bytes())
            output = base / "out" / "cards.csv"
            count, languages = build_csv(raw, output)
            first = output.read_bytes()
            build_csv(raw, output)
            self.assertEqual(output.read_bytes(), first)
            self.assertEqual(count, 2)
            self.assertEqual(languages, {"ru": 2})
            self.assertEqual(list(output.parent.iterdir()), [output])
            with output.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(reader.fieldnames, list(FIELDNAMES))
                self.assertEqual(len(reader.fieldnames), 50)
                records = list(reader)
            self.assertEqual([r["icsc_number"] for r in records], ["0001", "0087"])
            self.assertEqual(records[0], self.card("0001"))
            self.assertEqual(records[1], self.card("0087"))

    def test_bad_card_does_not_replace_existing_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base / "bad.html").write_text("<html><body>Service unavailable</body></html>", encoding="utf-8")
            output = base / "cards.csv"
            output.write_bytes(b"existing output")
            with self.assertRaisesRegex(ValueError, "CSV was not written"):
                build_csv(base, output)
            self.assertEqual(output.read_bytes(), b"existing output")

    def test_duplicate_document_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            content = (ILO / "0001.html").read_bytes()
            for name in ("first.html", "second.html"):
                (base / name).write_bytes(content)
            with self.assertRaisesRegex(ValueError, "duplicate doc_id"):
                build_csv(base, base / "cards.csv")
            self.assertFalse((base / "cards.csv").exists())

    def test_empty_input_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            with self.assertRaisesRegex(ValueError, "no HTML cards"):
                build_csv(base, base / "cards.csv")


if __name__ == "__main__":
    unittest.main()
