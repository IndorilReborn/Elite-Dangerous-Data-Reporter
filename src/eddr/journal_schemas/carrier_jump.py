from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class CarrierJump(JournalEntryBase):
    event: Literal[JournalEntryKind.CarrierJump] = JournalEntryKind.CarrierJump
    StarSystem: str
    SystemAddress: int
    StarPos: tuple[float, float, float]
