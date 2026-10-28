import json

import pytest

from chemsafety.schemas import Verdict, parse_answer

VALID = {
    "answerable": True,
    "verdict": "separate",
    "answer": "Хранить раздельно: окислитель и легковоспламеняющаяся жидкость.",
    "h_codes": ["H272", "H314"],
    "citations": [{"doc_id": "sigma_7697-37-2_65_en", "section": 10, "page": 6}],
}


def test_valid_answer_parses():
    answer, error = parse_answer(json.dumps(VALID))
    assert error is None
    assert answer.verdict is Verdict.SEPARATE


@pytest.mark.parametrize(
    "patch",
    [
        {"verdict": "maybe"},
        {"h_codes": ["314"]},
        {"extra_field": 1},
        {"answerable": False},
        {"citations": [{"doc_id": "x", "section": 17, "page": 1}]},
        {"answer": ""},
    ],
)
def test_invalid_answers_are_rejected(patch):
    answer, error = parse_answer(json.dumps({**VALID, **patch}))
    assert answer is None
    assert error


def test_refusal_needs_answerable_false():
    answer, _ = parse_answer(json.dumps({**VALID, "verdict": "refused"}))
    assert answer is None
    answer, _ = parse_answer(json.dumps({**VALID, "verdict": "refused", "answerable": False}))
    assert answer is not None


def test_markdown_wrapped_json_counts_as_invalid():
    answer, _ = parse_answer("```json\n" + json.dumps(VALID) + "\n```")
    assert answer is None
