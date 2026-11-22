"""Extract saved ILO/ICSC HTML cards into ONE CSV using only the standard library.

Run from the project root:
    python scripts/parse_ilo_cards.py
    python scripts/parse_ilo_cards.py --input data/raw/sds/ILO --output data/processed/substances.csv

One row per HTML document; 50 English column names in the requested order.
Source text remains in its original language (ru/en); no translation, network
requests, LLM calls, inferred chemical facts, or unit/temperature conversions.
Missing values are empty strings. Line breaks inside cells are CSV-quoted.
vapour_pressure and solubility_in_water retain the COMPLETE source property
line, including its units and measurement conditions. They are not silently
relabelled as measurements at 25 C / 21 C.
source is the path of the actual input file relative to --input.
doc_id is ilo_icsc_<number>_<lang>[_v<source-version>].
The classification text includes pictogram alt text, when present in the HTML.
transportation contains the complete transport block; un_classification its
UN-specific subsection. This deliberate overlap retains the source hierarchy.
Malformed/unrecognized cards and duplicate doc_ids abort the export rather
than silently creating incomplete rows. An existing CSV is replaced only
after every input has been parsed successfully.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

FIELDNAMES = (
    "name", "icsc_number", "cas", "un_number", "einecs",
    "specific_hazards", "preventive_measures", "fire_fighting",
    "inhalation_symptoms", "skin_contact_symptoms", "eye_contact_symptoms", "ingestion_symptoms",
    "inhalation_prevention", "skin_contact_prevention", "eye_contact_prevention", "ingestion_prevention",
    "inhalation_first_aid", "skin_contact_first_aid", "eye_contact_first_aid", "ingestion_first_aid",
    "spillage_disposal", "storage", "packaging", "classification_and_labelling",
    "transportation", "un_classification", "source",
    "physical_state_and_appearance", "physical_dangers", "chemical_dangers",
    "formula", "molecular_mass", "boiling_point", "melting_point",
    "relative_vapour_density_air_1", "flash_point", "auto_ignition_temperature",
    "explosive_limits_vol_percent_in_air", "vapour_pressure", "solubility_in_water",
    "routes_of_exposure", "effects_of_short_term_exposure", "inhalation_risk",
    "effects_of_long_term_or_repeated_exposure", "occupational_exposure_limits",
    "environment", "notes", "eu_classification", "lang", "doc_id",
)


def clean(text: str) -> str:
    """Normalize presentation whitespace, retaining explicit HTML line breaks."""
    return "\n".join(line for raw in text.splitlines() if (line := " ".join(raw.split())))


def key(text: str) -> str:
    return re.sub(r"[\W_]+", " ", text.casefold()).strip()


@dataclass
class Cell:
    tag: str
    parts: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return clean("".join(self.parts))


@dataclass
class Table:
    rows: list[list[Cell]] = field(default_factory=list)
    active_cell: Cell | None = None


class CardHTMLParser(HTMLParser):
    """Read table cells without relying on malformed legacy <p>/<b> nesting.

    Some ICSC files omit closing tags or contain stray </span> and </font>.
    Table/row/cell boundaries determine structure; inline tags never do.
    Nested table text also belongs to its containing cell.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[Table] = []
        self.stack: list[Table] = []
        self.inputs: dict[str, str] = {}
        self.selected_language = ""
        self.in_language_select = False
        self.hidden_tag: str | None = None

    def emit(self, text: str) -> None:
        for table in self.stack:
            if table.active_cell is not None:
                table.active_cell.parts.append(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"script", "style", "noscript"}:
            self.hidden_tag = tag
        if self.hidden_tag:
            return
        if tag == "input" and attributes.get("name") in {"p_card_id", "p_version"}:
            self.inputs[str(attributes["name"])] = attributes.get("value") or ""
        if tag == "select":
            self.in_language_select = attributes.get("name") == "p_lang"
        if tag == "option" and self.in_language_select and "selected" in attributes:
            self.selected_language = (attributes.get("value") or "").lower()
        if tag == "table":
            self.emit("\n")
            table = Table()
            self.tables.append(table)
            self.stack.append(table)
        elif tag == "tr" and self.stack:
            self.stack[-1].active_cell = None
            self.stack[-1].rows.append([])
        elif tag in {"td", "th"} and self.stack:
            table = self.stack[-1]
            if not table.rows:
                table.rows.append([])
            table.active_cell = Cell(tag)
            table.rows[-1].append(table.active_cell)
        elif tag in {"br", "p", "div", "li", "b", "strong"}:
            self.emit("\n")
        elif tag == "img" and attributes.get("alt"):
            self.emit("\n" + str(attributes["alt"]) + "\n")

    def handle_endtag(self, tag: str) -> None:
        if self.hidden_tag:
            if tag == self.hidden_tag:
                self.hidden_tag = None
            return
        if tag == "select":
            self.in_language_select = False
        if tag == "table" and self.stack:
            self.stack.pop()
            self.emit("\n")
        elif tag in {"td", "th", "tr"} and self.stack:
            self.stack[-1].active_cell = None
        elif tag in {"p", "div", "li"}:
            self.emit("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden_tag:
            self.emit(re.sub(r"\s+", " ", data))


# Literal section labels seen in the saved cards, with English equivalents.
SECTION_LABELS = {
    "spillage_disposal": ("ЛИКВИДАЦИЯ УТЕЧЕК", "SPILLAGE DISPOSAL"),
    "storage": ("ХРАНЕНИЕ", "STORAGE"),
    "packaging": ("УПАКОВКА", "PACKAGING"),
    "classification_and_labelling": ("КЛАССИФИКАЦИЯ И МАРКИРОВКА", "CLASSIFICATION & LABELLING"),
    "occupational_exposure_limits": ("Предельно-допустимые концентрации", "OCCUPATIONAL EXPOSURE LIMITS"),
    "environment": ("ОКРУЖАЮЩАЯ СРЕДА", "ENVIRONMENT"),
    "notes": ("ПРИМЕЧАНИЯ", "NOTES"),
}
SUBSECTION_LABELS = {
    "physical_state_and_appearance": ("Агрегатное Состояние; Внешний Вид", "PHYSICAL STATE; APPEARANCE"),
    "physical_dangers": ("Физические опасности", "PHYSICAL DANGERS"),
    "chemical_dangers": ("Химические опасности", "CHEMICAL DANGERS"),
    "routes_of_exposure": ("Пути воздействия", "ROUTES OF EXPOSURE"),
    "effects_of_short_term_exposure": (
        "Эффекты от кратковременного воздействия", "EFFECTS OF SHORT-TERM EXPOSURE",
    ),
    "inhalation_risk": ("Риск вдыхания", "INHALATION RISK"),
    "effects_of_long_term_or_repeated_exposure": (
        "Эффекты от длительного или повторяющегося воздействия",
        "EFFECTS OF LONG-TERM OR REPEATED EXPOSURE",
    ),
    "eu_classification": ("Классификация ЕС", "EU CLASSIFICATION"),
}
ROUTES = {
    "inhalation": ("Вдыхание", "Inhalation"),
    "skin_contact": ("Кожа", "Skin"),
    "eye_contact": ("Глаза", "Eyes"),
    "ingestion": ("Проглатывание", "Ingestion"),
}
PROPERTIES = {
    "formula": r"^(?:Формула|Formula)$",
    "molecular_mass": r"^(?:Молекулярная масса|Molecular mass|Molecular weight)$",
    "boiling_point": r"^(?:Температура кипения|Boiling point)\b",
    "melting_point": r"^(?:Температура плавления|Melting point)\b",
    "relative_vapour_density_air_1": r"^(?:Удельная плотность паров|Relative vapou?r density)\s*\(",
    "flash_point": r"^(?:Температура вспышки|Flash point)\b",
    "auto_ignition_temperature": r"(?:Температура самовоспламенения|Auto[ -]?ignition temperature)\b",
    "explosive_limits_vol_percent_in_air": r"^(?:Предел(?:ы)? взрываемости|Explosive limits)\b",
    "vapour_pressure": r"^(?:Давление пара|Давление паров|Vapou?r pressure)\b",
    "solubility_in_water": r"^(?:Растворимость в воде|Solubility in water)\b",
}


def lookup(labels: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return {key(label): column for column, variants in labels.items() for label in variants}


def extract_subsections(text: str, labels: dict[str, tuple[str, ...]]) -> dict[str, str]:
    headings = lookup(labels)
    result: dict[str, str] = {}
    active: str | None = None
    for line in text.splitlines():
        if key(line) in headings:
            active = headings[key(line)]
            result.setdefault(active, "")
        elif active:
            result[active] = clean(result[active] + "\n" + line)
    return result


def parse_card(path: Path, input_dir: Path) -> dict[str, str]:
    parser = CardHTMLParser()
    parser.feed(path.read_text(encoding="utf-8-sig"))
    parser.close()
    result = dict.fromkeys(FIELDNAMES, "")
    rows = [row for table in parser.tables for row in table.rows]
    cells = [cell for row in rows for cell in row]

    # The heading row contains the actual name and card number, unlike the
    # surrounding page's <html lang="en">, which also occurs on Russian cards.
    for row in rows:
        if len(row) >= 2 and (match := re.match(r"ICSC\s*:\s*(\d{4})\b", row[1].text)):
            result["name"] = row[0].text
            result["icsc_number"] = match[1]
            break
    if not result["name"] or not result["icsc_number"]:
        raise ValueError("missing ICSC name/number heading (not a supported card)")
    form_id = parser.inputs.get("p_card_id")
    if form_id and form_id != result["icsc_number"]:
        raise ValueError("ICSC number disagrees with the source form")

    headings = {key(cell.text) for cell in cells if cell.tag == "th"}
    content_language = "ru" if key("ОСОБЫЕ ОПАСНОСТИ") in headings else ""
    if key("ACUTE HAZARDS / SYMPTOMS") in headings or key("SPECIFIC HAZARDS") in headings:
        content_language = "en"
    language = parser.selected_language or content_language
    if language not in {"ru", "en"} or (content_language and language != content_language):
        raise ValueError("unsupported or inconsistent card language")
    result["lang"] = language
    result["source"] = path.relative_to(input_dir).as_posix()
    version = parser.inputs.get("p_version", "")
    if version and not version.isdigit():
        raise ValueError("invalid source version")
    result["doc_id"] = f"ilo_icsc_{result['icsc_number']}_{language}" + (f"_v{version}" if version else "")

    for cell in cells:
        for column, label in (("cas", "CAS"), ("un_number", "UN"), ("einecs", "EINECS")):
            match = re.match(rf"^{label}\s*(?:#|No\.?|number)?\s*:\s*(.*)$", cell.text, re.I | re.S)
            if match:
                result[column] = clean(match[1])

    seen: set[str] = set()
    sections = lookup(SECTION_LABELS)
    routes = lookup(ROUTES)
    for table in parser.tables:
        for index, row in enumerate(table.rows):
            if not row:
                continue
            label = key(row[0].text)
            if label in {key("ПОЖАР И ВЗРЫВ"), key("FIRE & EXPLOSION")}:
                if len(row) != 4:
                    raise ValueError("invalid fire/explosion table row")
                for column, cell in zip(
                    ("specific_hazards", "preventive_measures", "fire_fighting"), row[1:], strict=True
                ):
                    result[column] = cell.text
                seen.add("fire")
            if label in routes:
                if len(row) != 4:
                    raise ValueError(f"invalid exposure table row: {row[0].text}")
                route = routes[label]
                for suffix, cell in zip(("symptoms", "prevention", "first_aid"), row[1:], strict=True):
                    result[f"{route}_{suffix}"] = cell.text
                seen.add(route)
            for column_index, cell in enumerate(row):
                section = sections.get(key(cell.text)) if cell.tag == "th" else None
                if section:
                    if index + 1 >= len(table.rows) or column_index >= len(table.rows[index + 1]):
                        raise ValueError(f"missing data row for {section}")
                    result[section] = table.rows[index + 1][column_index].text
                    seen.add(section)

    for cell in cells:
        if cell.tag == "td":
            for column, value in extract_subsections(cell.text, SUBSECTION_LABELS).items():
                result[column] = value
                seen.add(column)

    # Classification and transport share a rowspan cell in the ILO template.
    classification = result["classification_and_labelling"]
    transport_labels = {key("Транспортировка"), key("Transportation"), key("Transport")}
    classification_lines = classification.splitlines()
    for index, line in enumerate(classification_lines):
        if key(line) in transport_labels:
            result["classification_and_labelling"] = clean("\n".join(classification_lines[:index]))
            result["transportation"] = clean("\n".join(classification_lines[index + 1:]))
            break
    result["un_classification"] = extract_subsections(
        result["transportation"], {"un": ("Классификация ООН", "UN CLASSIFICATION")}
    ).get("un", "")
    if key(result["transportation"]) in {key("Классификация ООН"), key("UN CLASSIFICATION")}:
        result["transportation"] = ""
    if key(result["classification_and_labelling"]) in {
        key("Согласно критериям СГС ООН"), key("According to UN GHS Criteria"),
    }:
        result["classification_and_labelling"] = ""

    # Only inspect the numeric-properties cell beside the physical-description
    # cell. This prevents matching property-like statements in notes or hazards.
    property_cells = []
    physical_heading = key(SUBSECTION_LABELS["physical_state_and_appearance"][0 if language == "ru" else 1])
    for row in rows:
        if len(row) == 2 and physical_heading in {key(line) for line in row[0].text.splitlines()}:
            property_cells.append(row[1])
    if len(property_cells) != 1:
        raise ValueError("expected one physical/chemical property cell")
    active_property: str | None = None
    for line in property_cells[0].text.splitlines():
        label, separator, value = line.partition(":")
        if not separator:
            if active_property and key(line) in {key("См. Примечания."), key("See Notes.")}:
                result[active_property] = clean(result[active_property] + "\n" + line)
            else:
                active_property = None
            continue
        active_property = None
        for column, pattern in PROPERTIES.items():
            if match := re.search(pattern, label.strip(), re.I):
                # Keep ALL qualifiers in pressure/solubility; also retain any
                # qualifiers on other property labels (e.g. boiling at 5 kPa).
                canonical = label.strip()
                if column in {"vapour_pressure", "solubility_in_water"} or match.start() > 0:
                    value = line
                elif column in {"boiling_point", "melting_point", "flash_point", "auto_ignition_temperature"}:
                    qualifier = canonical[match.end():].strip(" ,")
                    if qualifier:
                        value = qualifier + ": " + value.strip()
                result[column] = clean(result[column] + "\n" + value)
                active_property = column
                break

    required = {"fire", *ROUTES, *SECTION_LABELS, *SUBSECTION_LABELS}
    missing = required - seen
    if missing:
        raise ValueError("unrecognized/incomplete card structure: " + ", ".join(sorted(missing)))
    return result


def build_csv(input_dir: Path, output: Path) -> tuple[int, Counter[str]]:
    input_dir = input_dir.resolve()
    if not input_dir.is_dir():
        raise ValueError(f"input directory does not exist: {input_dir}")
    paths = sorted(
        (p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".html", ".htm"}),
        key=lambda p: p.relative_to(input_dir).as_posix(),
    )
    if not paths:
        raise ValueError(f"no HTML cards found in {input_dir}")
    if output.suffix.lower() != ".csv":
        raise ValueError("output must be a .csv file")
    records = []
    identifiers: dict[str, Path] = {}
    errors = []
    for path in paths:
        try:
            record = parse_card(path, input_dir)
            doc_id = record["doc_id"]
            if doc_id in identifiers:
                raise ValueError(f"duplicate doc_id {doc_id}: {identifiers[doc_id]}")
            identifiers[doc_id] = path
            records.append(record)
        except (ValueError, OSError) as exc:
            errors.append(f"{path.relative_to(input_dir)}: {exc}")
    if errors:
        raise ValueError(f"{len(errors)} card(s) failed; CSV was not written:\n" + "\n".join(errors))

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", newline="", dir=output.parent, suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(records)
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return len(records), Counter(row["lang"] for row in records)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument(
        "--input", type=Path, default=root / "data/raw/sds/ILO", help="directory of saved HTML cards"
    )
    cli.add_argument(
        "--output", type=Path, default=root / "data/processed/substances.csv", help="single output CSV"
    )
    args = cli.parse_args()
    try:
        count, languages = build_csv(args.input, args.output)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {count} rows, {len(FIELDNAMES)} columns to {args.output}")
    print("Languages: " + ", ".join(f"{lang}={n}" for lang, n in sorted(languages.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
