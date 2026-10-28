"""Одна команда сравнивает baseline и версии на одном golden set.

    uv run python -m eval.run                                   # все системы
    uv run python -m eval.run --systems baseline_closed_book --limit 10
    uv run python -m eval.run --final                           # финальный прогон, попадает в git

Результаты: reports/<run_id>/ (по файлу на систему, summary.md, summary.json), трейсы: traces/<run_id>.jsonl.
Системы, которые ещё не реализованы или не настроены, пропускаются с сообщением.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from chemsafety.config import load_settings
from chemsafety.systems import SYSTEMS, System, SystemOutput, build_system
from chemsafety.tracing import Tracer
from eval.dataset import GoldenItem, load_golden
from eval.metrics import ItemResult, summarize

METRIC_LABELS = {
    "n": "Вопросов",
    "valid_rate": "Валидный JSON",
    "verdict_accuracy": "Точность вердикта",
    "dangerous_error_rate": "Опасные ошибки (меньше — лучше)",
    "correct_refusal_rate": "Верные отказы",
    "false_refusal_rate": "Ложные отказы (меньше — лучше)",
    "citation_precision": "Precision ссылок",
    "citation_recall": "Recall ссылок",
    "retrieval_recall_at_k": "Recall@{k} поиска",
    "retrieval_mrr": "MRR поиска",
    "latency_p50_s": "Задержка p50, с",
    "latency_p95_s": "Задержка p95, с",
    "cost_usd": "Стоимость, $",
    "tokens_total": "Токенов всего",
}


def run_system(system: System, items: list[GoldenItem], tracer: Tracer | None = None) -> list[ItemResult]:
    results = []
    for item in items:
        if tracer is not None:
            tracer.context = {"system": system.name, "item_id": item.id}
        start = time.perf_counter()
        try:
            output = system.answer(item.question)
        except Exception as exc:  # ошибка на одном вопросе не должна ронять весь прогон
            output = SystemOutput(raw_text="", answer=None, error=f"{type(exc).__name__}: {exc}")
        output.latency_s = time.perf_counter() - start
        results.append(ItemResult(item=item, output=output))
    return results


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def format_summary(summaries: dict[str, dict[str, Any]], k: int) -> str:
    names = list(summaries)
    lines = ["| Метрика | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for key, label in METRIC_LABELS.items():
        cells = " | ".join(_fmt(summaries[name].get(key)) for name in names)
        lines.append(f"| {label.format(k=k)} | {cells} |")
    return "\n".join(lines)


def write_results(path: Path, results: list[ItemResult]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in results:
            out = r.output
            record = {
                "id": r.item.id,
                "type": r.item.type,
                "question": r.item.question,
                "expected": r.item.expected.model_dump(mode="json"),
                "evidence": [c.model_dump() for c in r.item.evidence],
                "answer": out.answer.model_dump(mode="json") if out.answer else None,
                "raw_text": out.raw_text,
                "error": out.error,
                "retrieved": None if out.retrieved is None else [c.model_dump() for c in out.retrieved],
                "prompt_tokens": out.prompt_tokens,
                "completion_tokens": out.completion_tokens,
                "cost_usd": out.cost_usd,
                "latency_s": out.latency_s,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Сравнение систем на golden set")
    parser.add_argument("--systems", default=",".join(SYSTEMS), help="через запятую; по умолчанию все")
    parser.add_argument("--golden", type=Path, help="по умолчанию paths.golden из configs/default.yaml")
    parser.add_argument("--limit", type=int, help="взять первые N вопросов")
    parser.add_argument("--final", action="store_true", help="записать в reports/final и traces/final")
    args = parser.parse_args(argv)

    names = [n.strip() for n in args.systems.split(",") if n.strip()]
    unknown = [n for n in names if n not in SYSTEMS]
    if unknown:
        parser.error(f"неизвестные системы {unknown}; есть: {', '.join(SYSTEMS)}")

    settings = load_settings()
    golden_path = args.golden or settings.paths["golden"]
    items = load_golden(golden_path)[: args.limit]
    if not items:
        print(f"Golden set пуст: {golden_path}. Формат описан в golden/README.md.")
        return 1

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    if args.final:
        out_dir = settings.paths["reports"] / "final"
        trace_path = settings.paths["traces"] / "final" / "trace.jsonl"
        trace_path.unlink(missing_ok=True)
    else:
        out_dir = settings.paths["reports"] / run_id
        trace_path = settings.paths["traces"] / f"{run_id}.jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)
    tracer = Tracer(trace_path, run_id)
    k = settings.retrieval["top_k"]

    summaries: dict[str, dict[str, Any]] = {}
    for name in names:
        try:
            system = build_system(name, settings, tracer)
        except (NotImplementedError, RuntimeError) as exc:
            print(f"[{name}] пропущена: {exc}")
            continue
        print(f"[{name}] {len(items)} вопросов…")
        results = run_system(system, items, tracer)
        write_results(out_dir / f"{name}.jsonl", results)
        summaries[name] = summarize(results, k)

    if not summaries:
        print("Ни одна система не запустилась.")
        return 1

    table = format_summary(summaries, k)
    (out_dir / "summary.md").write_text(
        f"Прогон {run_id}, golden set: {golden_path.name}\n\n{table}\n", encoding="utf-8"
    )
    (out_dir / "summary.json").write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n{table}\n\nОтчёт: {out_dir}\nТрейсы: {trace_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
