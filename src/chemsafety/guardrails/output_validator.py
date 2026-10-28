"""Проверка ответа перед показом пользователю.

1. Каждая ссылка указывает на чанк, который действительно был найден в этом запросе.
2. Консервативное правило: если check_compatibility вернул separate, restricted или insufficient_data,
   verdict=allowed запрещён.
При нарушении ответ заменяется на insufficient_data с объяснением, а нарушение пишется в трейс.
"""

from chemsafety.schemas import Answer, ScoredChunk, Verdict


def validate_output(answer: Answer, retrieved: list[ScoredChunk], tool_verdicts: list[Verdict]) -> Answer:
    raise NotImplementedError
