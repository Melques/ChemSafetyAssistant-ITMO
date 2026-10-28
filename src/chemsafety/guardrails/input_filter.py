"""Фильтр входа: отсекает атаки и запросы не по назначению до вызова агента.

Важно не перестараться. «Что будет, если смешать гипохлорит с кислотой?» — законный вопрос
о безопасности, на него нужно ответить по разделу 10 SDS. Поэтому меряем и долю успешных атак (ASR),
и долю ложных отказов на обычных вопросах.
"""

from enum import StrEnum

from pydantic import BaseModel


class InputCategory(StrEnum):
    OK = "ok"
    PROMPT_INJECTION = "prompt_injection"
    HARMFUL = "harmful"  # попытка получить помощь в намеренном создании опасности
    OFF_TOPIC = "off_topic"


class InputCheck(BaseModel):
    category: InputCategory
    reason: str


def check_input(question: str) -> InputCheck:
    raise NotImplementedError
