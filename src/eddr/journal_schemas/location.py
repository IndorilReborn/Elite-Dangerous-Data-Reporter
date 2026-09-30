from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Location(JournalEntryBase):
    event: Literal[JournalEntryKind.Location] = JournalEntryKind.Location
    StarSystem: str
    SystemAddress: int
    StarPos: tuple[float, float, float]
    Docked: bool
    StationName: str | None
    StationType: str | None
    MarketID: int | None
