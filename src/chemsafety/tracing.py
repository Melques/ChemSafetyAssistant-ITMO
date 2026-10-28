"""Трейсинг: каждый вызов модели и инструмента пишется строкой в JSONL.

Формат простой и без зависимостей. Если подключите Langfuse или Arize Phoenix,
сохраните этот интерфейс и отправляйте те же поля туда.
"""

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class Tracer:
    def __init__(self, path: Path, run_id: str):
        self.path = path
        self.run_id = run_id
        self.context: dict[str, Any] = {}  # eval.run кладёт сюда system и item_id
        path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, kind: str, name: str, **fields: Any) -> None:
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            **self.context,
            "kind": kind,
            "name": name,
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    @contextmanager
    def span(self, kind: str, name: str, **fields: Any) -> Iterator[dict[str, Any]]:
        """Замеряет длительность. Результат вызова допишите в возвращённый словарь."""
        start = time.perf_counter()
        extra: dict[str, Any] = {}
        try:
            yield extra
        except Exception as exc:
            extra["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            self.log(kind, name, **{**fields, **extra, "latency_s": round(time.perf_counter() - start, 4)})
