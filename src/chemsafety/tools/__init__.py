"""Блок 5: инструменты агента.

У каждого инструмента явный контракт: Pydantic-модели входа и выхода, ошибки в виде ToolError
и описанные в docstring побочные эффекты. Сводная таблица контрактов — docs/architecture.md.
"""

from typing import Literal

from pydantic import BaseModel


class ToolError(BaseModel):
    code: Literal["not_found", "ambiguous", "invalid_input", "unavailable"]
    message: str
