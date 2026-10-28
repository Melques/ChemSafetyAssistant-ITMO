"""Инструмент check_compatibility: можно ли хранить два вещества вместе. Считается по таблице, без LLM.

Правила — data/reference/trgs510_compatibility.csv (формат описан в data/README.md).
Пара, которой нет в таблице, даёт insufficient_data: система никогда не додумывает «можно».
Побочных эффектов нет.
"""

from typing import Literal

from pydantic import BaseModel

from chemsafety.schemas import Verdict
from chemsafety.tools import ToolError


class CheckCompatibilityInput(BaseModel):
    storage_class_a: str  # класс хранения TRGS 510 из раздела 7 SDS, например "3" или "8B"
    storage_class_b: str


class CheckCompatibilityOutput(BaseModel):
    verdict: Literal[Verdict.ALLOWED, Verdict.RESTRICTED, Verdict.SEPARATE, Verdict.INSUFFICIENT_DATA]
    rule_source: str
    note: str | None = None


def check_compatibility(inp: CheckCompatibilityInput) -> CheckCompatibilityOutput | ToolError:
    """invalid_input — класс хранения не из списка TRGS 510."""
    raise NotImplementedError
