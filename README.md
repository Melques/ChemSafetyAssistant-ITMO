# ChemSafetyAssistant-ITMO

LLM-ассистент по химической безопасности для склада и лаборатории. Отвечает на вопросы по паспортам
безопасности (SDS) и в каждом ответе ссылается на документ, раздел и страницу.
Курсовой проект «ML in Industry 2026», ИТМО.

## Задача

- **Пользователь:** кладовщик или лаборант, который принимает новую партию реактива.
- **Решение:** куда поставить вещество, с чем его можно хранить и какие СИЗ нужны.
- **Вход:** вопрос свободным текстом, например «Можно ли хранить азотную кислоту 65 % в одном шкафу с ацетоном?»
- **Выход:** JSON по схеме `Answer` ([src/chemsafety/schemas.py](src/chemsafety/schemas.py)): вердикт,
  классы опасности, H-коды, требования к хранению, СИЗ и ссылки `{doc_id, section, page}`.
- **Почему LLM:** SDS разных производителей — PDF с разной вёрсткой, формулировками и языками, вопросы
  задаются свободным текстом, ответ собирается из нескольких разделов и документов. То, что считается
  однозначно, система считает без LLM: совместимость — по таблице TRGS 510, GHS — запросом к базе.

## Данные

| Что | Где | Подробнее |
|---|---|---|
| SDS в PDF от нескольких производителей | `data/raw/sds/` | [data/README.md](data/README.md) |
| GHS-классификация из PubChem | `data/processed/ghs.sqlite` | `scripts/build_ghs_db.py` |
| Таблица совместного хранения TRGS 510 | `data/reference/trgs510_compatibility.csv` | [data/README.md](data/README.md) |
| Golden set | `golden/golden_set.jsonl` | [golden/README.md](golden/README.md) |

## Архитектура

Входной фильтр → агент с инструментами `search_sds`, `get_ghs`, `check_compatibility`,
`propose_storage_entry` → ответ по схеме → выходной фильтр → UI. Запись в журнал хранения выполняется
только после подтверждения человеком. Схема и контракты инструментов — [docs/architecture.md](docs/architecture.md).

## Модели

| Роль | Модель |
|---|---|
| Генерация, агент, LLM-судья | Qwen 3.8 27B (курсовая) |
| Эмбеддинги | BAAI/bge-m3 |
| Реранкер | BAAI/bge-reranker-v2-m3 |
| Разреженный поиск | BM25 |

## Как запустить

Нужен [uv](https://docs.astral.sh/uv/). Нужную версию Python он скачает сам.

```bash
git clone https://github.com/Melques/ChemSafetyAssistant-ITMO.git
cd ChemSafetyAssistant-ITMO
uv sync
cp .env.example .env        # вписать адрес, ключ и имя модели
uv run pytest

uv run python scripts/build_ghs_db.py
uv run python scripts/build_index.py

uv run python -m eval.run                        # все системы на golden set
uv run python -m eval.run --systems baseline_closed_book --limit 10
uv run python -m eval.run --final                # финальный прогон: reports/final и traces/final
```

Через Docker:

```bash
docker build -t chemsafety .
docker run --rm --env-file .env chemsafety
```

## Системы для сравнения

| Имя | Что это |
|---|---|
| `baseline_closed_book` | Qwen без поиска по документам |
| `baseline_bm25` | BM25 и шаблонный ответ из первого найденного чанка, без LLM |
| `v1_rag` | простой RAG: плотный поиск и генерация |
| `v2_agent` | фильтры, агент с инструментами, гибридный поиск |

## Результаты

Заполнить из `reports/final/summary.md`. Полный отчёт — [docs/evaluation_report.md](docs/evaluation_report.md),
безопасность — [docs/threat_model.md](docs/threat_model.md).

## Структура репозитория

```
configs/default.yaml        параметры модели, поиска, агента и пути
data/                       SDS, справочники и сгенерированные базы
golden/                     golden set и примеры для few-shot
src/chemsafety/
  schemas.py                схема ответа, чанки, ссылки
  config.py, llm.py, tracing.py, prompts.py
  parsing/                  PDF → страницы → разделы → чанки
  retrieval/                BM25, плотный поиск, гибрид, реранкер
  tools/                    инструменты агента с контрактами
  guardrails/               входной и выходной фильтры
  agent.py                  агент v2
  systems/                  baseline и версии для сравнения
  app.py                    UI для демо
eval/                       golden set, метрики, LLM-судья, запуск сравнения
scripts/                    сбор данных и индексов
docs/                       архитектура, модель угроз, отчёт
reports/, traces/           результаты прогонов; в git — только final/
tests/
```

## Кто что сделал

| Участник | Что сделал |
|---|---|
| Файрушин Булат | Создание шаблона репозитория |
| Барабанова Наталья | Сбор документов |
