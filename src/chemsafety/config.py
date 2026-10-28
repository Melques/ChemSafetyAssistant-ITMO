"""Настройки: configs/default.yaml плюс секреты и цены из .env."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "configs" / "default.yaml"


@dataclass(frozen=True)
class LLMSettings:
    base_url: str
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    structured_output: bool
    price_input_per_1m: float
    price_output_per_1m: float


@dataclass(frozen=True)
class Settings:
    llm: LLMSettings
    paths: dict[str, Path]
    retrieval: dict[str, Any]
    agent: dict[str, Any]


def load_settings(config_path: Path = DEFAULT_CONFIG) -> Settings:
    load_dotenv(ROOT / ".env")
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    llm = cfg["llm"]
    return Settings(
        llm=LLMSettings(
            base_url=os.environ.get("LLM_BASE_URL", ""),
            api_key=os.environ.get("LLM_API_KEY", ""),
            model=os.environ.get("LLM_MODEL", ""),
            temperature=llm["temperature"],
            max_tokens=llm["max_tokens"],
            structured_output=llm["structured_output"],
            price_input_per_1m=float(os.environ.get("PRICE_INPUT_PER_1M") or 0),
            price_output_per_1m=float(os.environ.get("PRICE_OUTPUT_PER_1M") or 0),
        ),
        paths={name: ROOT / rel for name, rel in cfg["paths"].items()},
        retrieval=cfg["retrieval"],
        agent=cfg["agent"],
    )
