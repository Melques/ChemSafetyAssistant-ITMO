"""PDF из data/raw/sds → страницы → разделы → чанки (data/processed/chunks.jsonl) → индексы поиска.

Шаги: chemsafety.parsing.pdf_to_text → chemsafety.parsing.sections → chemsafety.parsing.chunking,
затем chemsafety.retrieval. Это нереализованная заготовка для PDF; текущий
data/processed/substances.csv содержит карточки ILO и требует отдельной интеграции.

Запуск: uv run python scripts/build_index.py
"""


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
