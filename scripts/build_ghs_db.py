"""Сборка data/processed/ghs.sqlite из PubChem для инструмента get_ghs.

CID по CAS:  https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/cids/JSON
GHS по CID:  https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON?heading=GHS+Classification
Правила PubChem: не больше 5 запросов в секунду. Ответы кэшируйте, чтобы не скачивать повторно.

Запуск: uv run python scripts/build_ghs_db.py
"""


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
