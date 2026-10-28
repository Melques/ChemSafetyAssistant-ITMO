"""PDF из data/raw/sds → страницы → разделы → чанки (data/processed/chunks.jsonl) → индексы поиска.

Шаги: chemsafety.parsing.pdf_to_text → chemsafety.parsing.sections → chemsafety.parsing.chunking,
затем chemsafety.retrieval. Метаданные документов — из data/substances.csv.

Запуск: uv run python scripts/build_index.py
"""


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
