"""PDF → текст по страницам.

Кандидаты: PyMuPDF (быстрый, отдаёт номера страниц) и Docling (лучше справляется с таблицами).
Для сканов без текстового слоя нужен OCR (Tesseract). Библиотеку добавьте через `uv add`.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PageText:
    doc_id: str
    page: int  # с 1, как в PDF-просмотрщике
    text: str
    is_ocr: bool = False


def extract_pages(pdf_path: Path, doc_id: str) -> list[PageText]:
    raise NotImplementedError
