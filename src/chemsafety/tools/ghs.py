"""Инструмент get_ghs: GHS-классификация вещества из локальной базы, собранной из PubChem.

Это «запрос к структурированным данным» из блока 5. База: data/processed/ghs.sqlite,
собирается scripts/build_ghs_db.py. Побочных эффектов нет.

В PubChem у одного вещества бывает несколько уведомлений с разной классификацией (ECHA C&L).
Какое из них брать, решите явно и опишите в docs/architecture.md.
"""

from typing import Literal

from pydantic import BaseModel, Field

from chemsafety.schemas import CAS_PATTERN, HCode
from chemsafety.tools import ToolError


class GetGHSInput(BaseModel):
    cas: str = Field(pattern=CAS_PATTERN)


class GetGHSOutput(BaseModel):
    cas: str
    name: str
    pubchem_cid: int
    signal_word: Literal["Danger", "Warning"] | None
    h_codes: list[HCode]
    pictograms: list[str]  # GHS01 … GHS09
    source_url: str


def get_ghs(inp: GetGHSInput) -> GetGHSOutput | ToolError:
    """not_found — CAS нет в базе; ambiguous — у CAS несколько противоречивых записей."""
    raise NotImplementedError
