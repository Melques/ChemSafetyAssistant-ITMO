"""Агент версии v2: ограниченный вызов инструментов.

Правила (обоснование — docs/architecture.md):
- не больше settings.agent["max_steps"] шагов;
- доступны только search_sds, get_ghs, check_compatibility и propose_storage_entry;
- confirm_storage_entry агенту не передаётся: запись в журнал подтверждает человек в UI;
- каждый вызов модели и инструмента пишется в трейс.

Схемы инструментов для function calling берутся из model_json_schema() их входных моделей.
"""

from chemsafety.llm import LLMClient
from chemsafety.schemas import Answer, ScoredChunk, Verdict
from chemsafety.tracing import Tracer


class Agent:
    def __init__(self, llm: LLMClient, tracer: Tracer, max_steps: int):
        raise NotImplementedError

    def run(self, question: str) -> tuple[Answer | None, str, list[ScoredChunk], list[Verdict]]:
        """Возвращает ответ, сырой текст модели, найденные чанки и вердикты check_compatibility.

        Чанки и вердикты нужны выходному фильтру для проверки ссылок и консервативного правила.
        """
        raise NotImplementedError
