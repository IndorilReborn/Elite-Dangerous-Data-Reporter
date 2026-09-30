from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Docked(JournalEntryBase):
    event: Literal[JournalEntryKind.Docked] = JournalEntryKind.Docked
    StationType: str
    StationName: str
    MarketID: int
