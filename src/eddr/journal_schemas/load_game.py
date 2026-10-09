from typing import Literal

from pydantic import Field

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class LoadGame(JournalEntryBase):
    event: Literal[JournalEntryKind.LoadGame] = JournalEntryKind.LoadGame
    Horizons: bool
    Odyssey: bool | None = Field(default=None)
