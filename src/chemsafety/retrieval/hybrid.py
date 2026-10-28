"""Гибридный поиск: объединение выдач BM25 и плотного поиска через Reciprocal Rank Fusion.

RRF: score(d) = Σ_i 1 / (k + rank_i(d)), rank с 1; k — retrieval.rrf_k в configs/default.yaml.
"""


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """rankings — списки chunk_id, отсортированные по убыванию релевантности."""
    raise NotImplementedError
