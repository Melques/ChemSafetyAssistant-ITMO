"""Общие модели данных: чанки SDS, ссылки на источник и структурированный ответ ассистента."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

CAS_PATTERN = r"^\d{2,7}-\d{2}-\d$"
HCode = Annotated[str, Field(pattern=r"^(EU)?H\d{3}[A-Za-z]*$")]


class Verdict(StrEnum):
    ALLOWED = "allowed"  # можно хранить вместе
    RESTRICTED = "restricted"  # можно при условиях из storage_requirements
    SEPARATE = "separate"  # хранить раздельно
    NOT_APPLICABLE = "not_applicable"  # вопрос не о совместимости
    INSUFFICIENT_DATA = "insufficient_data"  # ответа нет в данных
    REFUSED = "refused"  # запрос вне назначения системы или направлен на вред


REFUSAL_VERDICTS = frozenset({Verdict.INSUFFICIENT_DATA, Verdict.REFUSED})


class Citation(BaseModel):
    """Место в SDS. Тем же форматом в golden set размечается evidence."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    section: int = Field(ge=1, le=16)
    page: int = Field(ge=1)


class Chunk(BaseModel):
    """Фрагмент SDS с метаданными. Не пересекает границу раздела."""

    chunk_id: str
    doc_id: str
    vendor: str
    substance: str
    cas: str | None = Field(default=None, pattern=CAS_PATTERN)
    concentration: str | None = None
    lang: str
    section: int = Field(ge=1, le=16)
    subsection: str | None = None
    page: int = Field(ge=1)  # страница, на которой чанк начинается
    text: str


class ScoredChunk(BaseModel):
    chunk: Chunk
    score: float


class Answer(BaseModel):
    """Ответ ассистента. Доля ответов, прошедших эту схему, — метрика блока 1."""

    model_config = ConfigDict(extra="forbid")

    answerable: bool
    verdict: Verdict
    answer: str = Field(min_length=1)
    hazard_classes: list[str] = Field(default_factory=list)
    h_codes: list[HCode] = Field(default_factory=list)
    storage_requirements: list[str] = Field(default_factory=list)
    ppe: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _refusal_is_consistent(self) -> "Answer":
        if self.answerable == (self.verdict in REFUSAL_VERDICTS):
            raise ValueError(
                "answerable=false ставится вместе с verdict insufficient_data или refused, и только с ними"
            )
        return self


def parse_answer(text: str) -> tuple[Answer | None, str | None]:
    """Строгий разбор ответа модели: без чистки markdown и без повторных запросов."""
    try:
        return Answer.model_validate_json(text), None
    except ValidationError as exc:
        return None, str(exc)
