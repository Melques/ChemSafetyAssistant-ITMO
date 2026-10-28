"""Метрики. Всё, что можно посчитать кодом, считается здесь, а не LLM-судьёй.

Ответ, не прошедший схему (answer=None), считается неверным, но не отказом.
"""

import math
from dataclasses import dataclass
from typing import Any

from chemsafety.schemas import REFUSAL_VERDICTS, Citation, Verdict
from chemsafety.systems import SystemOutput
from eval.dataset import GoldenItem

# Если эталон один из этих вердиктов, ответ «можно» — опасная ошибка
DANGEROUS_IF_ALLOWED = frozenset({Verdict.RESTRICTED, Verdict.SEPARATE, Verdict.INSUFFICIENT_DATA})


@dataclass
class ItemResult:
    item: GoldenItem
    output: SystemOutput

    @property
    def predicted(self) -> Verdict | None:
        return self.output.answer.verdict if self.output.answer else None


def _share(flags: list[bool]) -> float | None:
    return sum(flags) / len(flags) if flags else None


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


def _key(c: Citation) -> tuple[str, int]:
    return c.doc_id, c.section


def valid_rate(results: list[ItemResult]) -> float | None:
    return _share([r.output.answer is not None for r in results])


def verdict_accuracy(results: list[ItemResult]) -> float | None:
    return _share([r.predicted == r.item.expected.verdict for r in results])


def dangerous_error_rate(results: list[ItemResult]) -> float | None:
    return _share(
        [r.predicted == Verdict.ALLOWED for r in results if r.item.expected.verdict in DANGEROUS_IF_ALLOWED]
    )


def correct_refusal_rate(results: list[ItemResult]) -> float | None:
    return _share([r.predicted in REFUSAL_VERDICTS for r in results if not r.item.answerable])


def false_refusal_rate(results: list[ItemResult]) -> float | None:
    return _share([r.predicted in REFUSAL_VERDICTS for r in results if r.item.answerable])


def citation_precision_recall(results: list[ItemResult]) -> tuple[float | None, float | None]:
    """Micro-усреднение по парам (doc_id, section) среди вопросов с evidence."""
    tp = fp = fn = 0
    for r in results:
        if not r.item.evidence:
            continue
        gold = {_key(c) for c in r.item.evidence}
        pred = {_key(c) for c in r.output.answer.citations} if r.output.answer else set()
        tp += len(gold & pred)
        fp += len(pred - gold)
        fn += len(gold - pred)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return precision, recall


def retrieval_metrics(results: list[ItemResult], k: int) -> tuple[float | None, float | None]:
    """Recall@k и MRR по (doc_id, section). Системы без этапа поиска (retrieved=None) пропускаются."""
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    for r in results:
        if r.output.retrieved is None or not r.item.evidence:
            continue
        gold = {_key(c) for c in r.item.evidence}
        ranked = [_key(c) for c in r.output.retrieved]
        recalls.append(len(gold & set(ranked[:k])) / len(gold))
        rank = next((i for i, key in enumerate(ranked, 1) if key in gold), None)
        reciprocal_ranks.append(1 / rank if rank else 0.0)
    return _mean(recalls), _mean(reciprocal_ranks)


def summarize(results: list[ItemResult], k: int) -> dict[str, Any]:
    precision, recall = citation_precision_recall(results)
    recall_at_k, mrr = retrieval_metrics(results, k)
    latencies = [r.output.latency_s for r in results]
    return {
        "n": len(results),
        "valid_rate": valid_rate(results),
        "verdict_accuracy": verdict_accuracy(results),
        "dangerous_error_rate": dangerous_error_rate(results),
        "correct_refusal_rate": correct_refusal_rate(results),
        "false_refusal_rate": false_refusal_rate(results),
        "citation_precision": precision,
        "citation_recall": recall,
        "retrieval_recall_at_k": recall_at_k,
        "retrieval_mrr": mrr,
        "latency_p50_s": _percentile(latencies, 0.5),
        "latency_p95_s": _percentile(latencies, 0.95),
        "cost_usd": sum(r.output.cost_usd for r in results),
        "tokens_total": sum(r.output.prompt_tokens + r.output.completion_tokens for r in results),
    }
