import pytest

from chemsafety.schemas import Verdict
from eval.dataset import ItemType
from eval.judge import cohen_kappa
from eval.metrics import (
    ItemResult,
    citation_precision_recall,
    correct_refusal_rate,
    dangerous_error_rate,
    false_refusal_rate,
    retrieval_metrics,
    valid_rate,
    verdict_accuracy,
)


def test_invalid_output_counts_as_wrong(make_item, make_output):
    results = [
        ItemResult(make_item("q1"), make_output(Verdict.SEPARATE)),
        ItemResult(make_item("q2"), make_output(None)),
    ]
    assert valid_rate(results) == 0.5
    assert verdict_accuracy(results) == 0.5


def test_allowed_instead_of_separate_is_dangerous(make_item, make_output):
    results = [
        ItemResult(make_item("q1", Verdict.SEPARATE), make_output(Verdict.ALLOWED)),
        ItemResult(make_item("q2", Verdict.RESTRICTED), make_output(Verdict.SEPARATE)),
        ItemResult(make_item("q3", Verdict.ALLOWED), make_output(Verdict.ALLOWED)),
    ]
    assert dangerous_error_rate(results) == 0.5


def test_refusal_rates(make_item, make_output):
    unanswerable = make_item("q1", Verdict.INSUFFICIENT_DATA, type=ItemType.UNANSWERABLE)
    answerable = make_item("q2", Verdict.NOT_APPLICABLE, type=ItemType.FACT)
    results = [
        ItemResult(unanswerable, make_output(Verdict.INSUFFICIENT_DATA)),
        ItemResult(answerable, make_output(Verdict.REFUSED)),
    ]
    assert correct_refusal_rate(results) == 1.0
    assert false_refusal_rate(results) == 1.0


def test_citations_ignore_page_and_use_doc_and_section(make_item, make_output):
    item = make_item(evidence=(("doc1", 7, 2), ("doc2", 10, 5)))
    output = make_output(Verdict.SEPARATE, citations=(("doc1", 7, 3), ("doc3", 8, 1)))
    assert citation_precision_recall([ItemResult(item, output)]) == (0.5, 0.5)


def test_retrieval_recall_and_mrr(make_item, make_output):
    item = make_item(evidence=(("doc1", 7, 2),))
    output = make_output(Verdict.SEPARATE, retrieved=(("doc2", 8, 1), ("doc1", 7, 2)))
    results = [ItemResult(item, output)]
    assert retrieval_metrics(results, k=1) == (0.0, 0.5)
    assert retrieval_metrics(results, k=2) == (1.0, 0.5)


def test_retrieval_skipped_for_systems_without_search(make_item, make_output):
    results = [ItemResult(make_item(), make_output(Verdict.SEPARATE))]
    assert retrieval_metrics(results, k=5) == (None, None)


def test_cohen_kappa():
    assert cohen_kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == pytest.approx(0.0)
