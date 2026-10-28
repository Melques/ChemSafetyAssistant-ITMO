"""Разреженный поиск BM25: основа baseline (б) и половина гибридного поиска. Кандидат: `uv add rank-bm25`."""

from chemsafety.schemas import Chunk, ScoredChunk


class BM25Index:
    def __init__(self, chunks: list[Chunk]):
        raise NotImplementedError

    def search(
        self, query: str, top_k: int, cas: str | None = None, section: int | None = None
    ) -> list[ScoredChunk]:
        """Фильтры cas и section применяются до ранжирования."""
        raise NotImplementedError
