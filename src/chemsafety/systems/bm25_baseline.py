"""Baseline (б): BM25 по чанкам SDS и шаблонный ответ из первого найденного чанка, без LLM.

Что сделать:
- загрузить чанки из settings.paths["chunks"] и построить chemsafety.retrieval.bm25.BM25Index;
- answer(): найти top_k чанков, вернуть Answer(answerable=True, verdict=not_applicable,
  answer=<текст первого чанка>, citations=[его doc_id, section, page]);
- в SystemOutput.retrieved положить всю выдачу, чтобы eval посчитал Recall@k и MRR.
"""

from chemsafety.config import Settings
from chemsafety.systems import SystemOutput
from chemsafety.tracing import Tracer


class BM25Baseline:
    name = "baseline_bm25"

    def __init__(self, settings: Settings, tracer: Tracer):
        raise NotImplementedError("нужны чанки из scripts/build_index.py и chemsafety.retrieval.bm25")

    def answer(self, question: str) -> SystemOutput:
        raise NotImplementedError
