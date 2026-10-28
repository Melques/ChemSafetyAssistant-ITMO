"""Golden set: формат записи и загрузка. Правила разметки — golden/README.md."""

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from chemsafety.schemas import REFUSAL_VERDICTS, Citation, HCode, Verdict


class ItemType(StrEnum):
    FACT = "fact"
    PPE = "ppe"
    STORAGE = "storage"
    COMPATIBILITY = "compatibility"
    FIRST_AID = "first_aid"
    MULTI_DOC = "multi_doc"
    UNANSWERABLE = "unanswerable"
    ATTACK = "attack"


class Expected(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    answer: str | None = None  # эталонный ответ для LLM-судьи
    h_codes: list[HCode] = Field(default_factory=list)


class GoldenItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: ItemType
    question: str
    expected: Expected
    evidence: list[Citation] = Field(default_factory=list)
    answerable: bool
    notes: str | None = None

    @model_validator(mode="after")
    def _labels_are_consistent(self) -> "GoldenItem":
        if self.answerable == (self.expected.verdict in REFUSAL_VERDICTS):
            raise ValueError("answerable не согласован с expected.verdict")
        if self.answerable and self.type != ItemType.ATTACK and not self.evidence:
            raise ValueError("у вопроса с ответом должен быть evidence")
        return self


def load_golden(path: Path) -> list[GoldenItem]:
    items: list[GoldenItem] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                items.append(GoldenItem.model_validate_json(line))
            except ValidationError as exc:
                raise ValueError(f"{path}:{line_no}: {exc}") from exc
    ids = [item.id for item in items]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"{path}: повторяются id {duplicates}")
    return items
