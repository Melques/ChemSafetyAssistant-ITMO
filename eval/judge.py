"""LLM-судья для свободного текста (поле answer) и его проверка по ручной разметке.

Судья оценивает только то, что нельзя проверить кодом: правильность ответа относительно эталона
и опору на процитированные фрагменты (faithfulness). Вердикты, H-коды и ссылки считает eval.metrics.

Проверка судьи: вручную разметьте 40+ ответов (верно/неверно), прогоните судью на тех же ответах
и посчитайте cohen_kappa. Если судья — та же Qwen, учтите предпочтение собственных ответов.
"""

from collections.abc import Hashable, Sequence

from pydantic import BaseModel


class JudgeVerdict(BaseModel):
    correct: bool
    faithful: bool
    reason: str


def judge_answer(question: str, reference: str, candidate: str, cited_texts: list[str]) -> JudgeVerdict:
    raise NotImplementedError


def cohen_kappa(a: Sequence[Hashable], b: Sequence[Hashable]) -> float:
    """Согласие двух разметчиков с поправкой на случайное совпадение. Подходит и для «судья против людей»."""
    if len(a) != len(b) or not a:
        raise ValueError("нужны две непустые разметки одинаковой длины")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    labels = set(a) | set(b)
    expected = sum((list(a).count(label) / n) * (list(b).count(label) / n) for label in labels)
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)
