"""Действие с последствиями: запись вещества в журнал хранения (data/processed/storage_log.sqlite).

Агент может только предложить запись через propose_storage_entry, журнал при этом не меняется.
Запись появляется только после confirm_storage_entry. Его вызывает UI, когда человек нажал
«Подтвердить»; агенту этот инструмент не передаётся.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from chemsafety.schemas import CAS_PATTERN, Citation
from chemsafety.tools import ToolError


class StorageEntryProposal(BaseModel):
    substance: str
    cas: str = Field(pattern=CAS_PATTERN)
    location: str  # шкаф или стеллаж
    quantity: str
    justification: str  # почему это место подходит
    citations: list[Citation]


class PendingAction(BaseModel):
    action_id: str
    proposal: StorageEntryProposal
    created_at: datetime


def propose_storage_entry(proposal: StorageEntryProposal) -> PendingAction | ToolError:
    """Побочный эффект: только сохранение черновика действия. Журнал не меняется."""
    raise NotImplementedError


def confirm_storage_entry(action_id: str, approved_by: str) -> None:
    """Побочный эффект: запись в журнал хранения. Вызывается только из UI."""
    raise NotImplementedError
