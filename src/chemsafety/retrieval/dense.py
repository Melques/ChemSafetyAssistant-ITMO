"""Плотный поиск по эмбеддингам. Модель — retrieval.embedding_model в configs/default.yaml.

Кандидаты: sentence-transformers для эмбеддингов, Qdrant, Chroma или FAISS для хранения векторов.
"""

from chemsafety.schemas import Chunk, ScoredChunk


class DenseIndex:
    def __init__(self, chunks: list[Chunk], model_name: str):
        raise NotImplementedError

    def search(
        self, query: str, top_k: int, cas: str | None = None, section: int | None = None
    ) -> list[ScoredChunk]:
        raise NotImplementedError
