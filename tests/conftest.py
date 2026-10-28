import pytest

from chemsafety.schemas import REFUSAL_VERDICTS, Answer, Citation, Verdict
from chemsafety.systems import SystemOutput
from eval.dataset import Expected, GoldenItem, ItemType


def _citations(triples) -> list[Citation]:
    return [Citation(doc_id=d, section=s, page=p) for d, s, p in triples]


@pytest.fixture
def make_item():
    def make(
        id="q1",
        verdict=Verdict.SEPARATE,
        evidence=(("doc1", 7, 2),),
        question="вопрос",
        type=ItemType.COMPATIBILITY,
    ) -> GoldenItem:
        answerable = verdict not in REFUSAL_VERDICTS
        return GoldenItem(
            id=id,
            type=type,
            question=question,
            expected=Expected(verdict=verdict),
            evidence=_citations(evidence) if answerable else [],
            answerable=answerable,
        )

    return make


@pytest.fixture
def make_output():
    def make(verdict=None, citations=(), retrieved=None) -> SystemOutput:
        answer = None
        if verdict is not None:
            answer = Answer(
                answerable=verdict not in REFUSAL_VERDICTS,
                verdict=verdict,
                answer="ответ",
                citations=_citations(citations),
            )
        return SystemOutput(
            raw_text="", answer=answer, retrieved=None if retrieved is None else _citations(retrieved)
        )

    return make
