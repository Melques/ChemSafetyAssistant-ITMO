"""Baseline (а): Qwen отвечает без поиска по документам.

Показывает, сколько модель выдумывает без SDS: ссылок у неё нет, вердикты — из памяти.
"""

from chemsafety.config import Settings
from chemsafety.llm import LLMClient
from chemsafety.prompts import CLOSED_BOOK_SYSTEM
from chemsafety.schemas import Answer, parse_answer
from chemsafety.systems import SystemOutput
from chemsafety.tracing import Tracer


class ClosedBookBaseline:
    name = "baseline_closed_book"

    def __init__(self, settings: Settings, tracer: Tracer):
        self.llm = LLMClient(settings.llm, tracer)

    def answer(self, question: str) -> SystemOutput:
        messages = [
            {"role": "system", "content": CLOSED_BOOK_SYSTEM},
            {"role": "user", "content": question},
        ]
        result = self.llm.chat(messages, schema=Answer, name=self.name)
        answer, error = parse_answer(result.text)
        return SystemOutput(
            raw_text=result.text,
            answer=answer,
            error=error,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            cost_usd=result.cost_usd,
        )
