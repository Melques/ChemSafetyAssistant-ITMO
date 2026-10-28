"""Клиент курсовой модели через OpenAI-совместимый API. Каждый вызов попадает в трейс."""

from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from chemsafety.config import LLMSettings
from chemsafety.tracing import Tracer


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


def json_schema_format(model: type[BaseModel]) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {"name": model.__name__, "schema": model.model_json_schema()},
    }


class LLMClient:
    def __init__(self, settings: LLMSettings, tracer: Tracer):
        if not settings.base_url or not settings.model:
            raise RuntimeError(
                "не заданы LLM_BASE_URL и LLM_MODEL: скопируйте .env.example в .env и заполните"
            )
        self.settings = settings
        self.tracer = tracer
        self._client = OpenAI(base_url=settings.base_url, api_key=settings.api_key or "EMPTY")

    def chat(
        self, messages: list[dict[str, str]], *, schema: type[BaseModel] | None = None, name: str = "chat"
    ) -> LLMResult:
        kwargs: dict[str, Any] = {}
        if schema is not None and self.settings.structured_output:
            kwargs["response_format"] = json_schema_format(schema)

        with self.tracer.span("llm", name, model=self.settings.model, messages=messages) as span:
            response = self._client.chat.completions.create(
                model=self.settings.model,
                messages=messages,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
                **kwargs,
            )
            text = response.choices[0].message.content or ""
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            cost = (
                prompt_tokens * self.settings.price_input_per_1m
                + completion_tokens * self.settings.price_output_per_1m
            ) / 1_000_000
            span.update(
                output=text, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, cost_usd=cost
            )
        return LLMResult(text, prompt_tokens, completion_tokens, cost)
