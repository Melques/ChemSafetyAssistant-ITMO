"""Нарезка разделов на чанки (chemsafety.schemas.Chunk). Чанк не пересекает границу раздела.

Текущие карточки ILO находятся в data/processed/substances.csv; интеграция пока не реализована.
"""

from dataclasses import dataclass

from chemsafety.parsing.sections import Section
from chemsafety.schemas import Chunk


@dataclass
class DocMeta:
    doc_id: str
    vendor: str
    substance: str
    cas: str | None
    concentration: str | None
    lang: str


def chunk_sections(sections: list[Section], meta: DocMeta, max_chars: int) -> list[Chunk]:
    raise NotImplementedError
