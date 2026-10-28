"""Версия v2: входной фильтр → агент с инструментами → выходной фильтр.

Состав: chemsafety.guardrails.input_filter, chemsafety.agent, chemsafety.guardrails.output_validator.
"""

from chemsafety.config import Settings
from chemsafety.systems import SystemOutput
from chemsafety.tracing import Tracer


class AgentV2:
    name = "v2_agent"

    def __init__(self, settings: Settings, tracer: Tracer):
        raise NotImplementedError("нужны chemsafety.agent, chemsafety.tools и chemsafety.guardrails")

    def answer(self, question: str) -> SystemOutput:
        raise NotImplementedError
