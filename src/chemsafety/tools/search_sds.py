"""Инструмент search_sds: гибридный поиск по чанкам SDS. Побочных эффектов нет."""

from pydantic import BaseModel, Field

from chemsafety.schemas import CAS_PATTERN, ScoredChunk
from chemsafety.tools import ToolError


class SearchSDSInput(BaseModel):
    query: str = Field(min_length=3)
    cas: str | None = Field(default=None, pattern=CAS_PATTERN)
    section: int | None = Field(default=None, ge=1, le=16)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchSDSOutput(BaseModel):
    hits: list[ScoredChunk]


def search_sds(inp: SearchSDSInput) -> SearchSDSOutput | ToolError:
    """not_found — для указанного cas нет ни одного SDS.

    Пустой hits — документы есть, но ничего не нашлось.
    """
    raise NotImplementedError
