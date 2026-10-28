"""Переранжирование кандидатов cross-encoder'ом. Модель — retrieval.reranker_model в configs/default.yaml."""

from chemsafety.schemas import ScoredChunk


class Reranker:
    def __init__(self, model_name: str):
        raise NotImplementedError

    def rerank(self, query: str, candidates: list[ScoredChunk], top_k: int) -> list[ScoredChunk]:
        raise NotImplementedError
