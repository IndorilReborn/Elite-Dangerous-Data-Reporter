from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class CarrierStats(JournalEntryBase):
    event: Literal[JournalEntryKind.CarrierStats] = JournalEntryKind.CarrierStats
    CarrierID: int
    Name: str
    Callsign: str
