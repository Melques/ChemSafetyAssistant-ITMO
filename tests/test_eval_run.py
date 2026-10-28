import json

import pytest

from chemsafety.schemas import Verdict
from eval.dataset import load_golden
from eval.metrics import summarize
from eval.run import format_summary, main, run_system


class FakeSystem:
    name = "fake"

    def __init__(self, make_output):
        self.make_output = make_output

    def answer(self, question):
        if question == "boom":
            raise RuntimeError("сломалось")
        return self.make_output(Verdict.SEPARATE, citations=(("doc1", 7, 2),))


def test_run_system_survives_errors(make_item, make_output):
    items = [make_item("q1"), make_item("q2", question="boom")]
    results = run_system(FakeSystem(make_output), items)
    assert results[0].output.answer is not None
    assert results[1].output.error.startswith("RuntimeError")
    assert all(r.output.latency_s >= 0 for r in results)


def test_summary_table_has_a_row_per_metric(make_item, make_output):
    results = run_system(FakeSystem(make_output), [make_item("q1")])
    table = format_summary({"fake": summarize(results, k=5)}, k=5)
    assert "| Валидный JSON | 1.000 |" in table
    assert "| Recall@5 поиска | — |" in table


def test_load_golden_rejects_inconsistent_labels(tmp_path):
    record = {
        "id": "q1",
        "type": "fact",
        "question": "?",
        "expected": {"verdict": "insufficient_data"},
        "answerable": True,
    }
    path = tmp_path / "golden.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="answerable"):
        load_golden(path)


def test_main_reports_empty_golden_set(tmp_path, capsys):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    assert main(["--golden", str(path)]) == 1
    assert "Golden set пуст" in capsys.readouterr().out
