from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class FSDJump(JournalEntryBase):
    event: Literal[JournalEntryKind.FSDJump] = JournalEntryKind.FSDJump
    StarSystem: str
    SystemAddress: int
    StarPos: tuple[float, float, float]
