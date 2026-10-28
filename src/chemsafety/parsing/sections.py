"""Разбиение SDS на 16 разделов.

Заголовки бывают вида «SECTION 7», «РАЗДЕЛ 7», «ABSCHNITT 7», подразделы — «7.1», «7.2».
Качество проверяется на 15–20 вручную размеченных документах: доля верно найденных границ
разделов и правильность номеров страниц.
"""

from dataclasses import dataclass

from chemsafety.parsing.pdf_to_text import PageText


@dataclass
class Section:
    doc_id: str
    number: int  # 1..16
    title: str
    subsection: str | None
    page_start: int
    page_end: int
    text: str


def split_sections(pages: list[PageText]) -> list[Section]:
    raise NotImplementedError
