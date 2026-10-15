from typing import Literal

from pydantic import Field

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Location(JournalEntryBase):
    event: Literal[JournalEntryKind.Location] = JournalEntryKind.Location
    StarSystem: str
    SystemAddress: int
    StarPos: tuple[float, float, float]
    Docked: bool
    StationName: str | None = Field(default=None)
    StationType: str | None = Field(default=None)
    MarketID: int | None = Field(default=None)
