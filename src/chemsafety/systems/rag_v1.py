"""Версия v1: простой RAG.

Что сделать:
- чанки фиксированной длины и плотный поиск (chemsafety.retrieval.dense);
- найденные фрагменты передать модели в <document id=...> с промптом chemsafety.prompts.RAG_SYSTEM;
- ответ разобрать через chemsafety.schemas.parse_answer;
- в SystemOutput.retrieved положить выдачу поиска.

Улучшения поиска (CAS-фильтр, гибрид, реранкер, выбор раздела) лучше делать отдельными флагами:
так их вклад виден в абляциях.
"""

from chemsafety.config import Settings
from chemsafety.systems import SystemOutput
from chemsafety.tracing import Tracer


class RagV1:
    name = "v1_rag"

    def __init__(self, settings: Settings, tracer: Tracer):
        raise NotImplementedError("нужны индекс поиска и chemsafety.retrieval")

    def answer(self, question: str) -> SystemOutput:
        raise NotImplementedError
