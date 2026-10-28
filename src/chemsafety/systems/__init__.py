"""Системы, которые сравнивает eval.run. Новая версия — это новый класс и строка в SYSTEMS."""

import importlib
from dataclasses import dataclass
from typing import Protocol

from chemsafety.config import Settings
from chemsafety.schemas import Answer, Citation
from chemsafety.tracing import Tracer


@dataclass
class SystemOutput:
    raw_text: str  # ответ модели до разбора: нужен для анализа ошибок формата
    answer: Answer | None  # None, если ответ не прошёл схему Answer
    error: str | None = None
    # Ранжированная выдача поиска для Recall@k и MRR. None — у системы нет этапа поиска.
    retrieved: list[Citation] | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0  # заполняет eval.run


class System(Protocol):
    name: str

    def answer(self, question: str) -> SystemOutput: ...


SYSTEMS = {
    "baseline_closed_book": "chemsafety.systems.closed_book:ClosedBookBaseline",
    "baseline_bm25": "chemsafety.systems.bm25_baseline:BM25Baseline",
    "v1_rag": "chemsafety.systems.rag_v1:RagV1",
    "v2_agent": "chemsafety.systems.agent_v2:AgentV2",
}


def build_system(name: str, settings: Settings, tracer: Tracer) -> System:
    module_name, class_name = SYSTEMS[name].split(":")
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls(settings, tracer)
