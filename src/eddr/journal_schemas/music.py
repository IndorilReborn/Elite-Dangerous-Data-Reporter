from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class MusicEntry(JournalEntryBase):
    event: Literal[JournalEntryKind.Music] = JournalEntryKind.Music
    MusicTrack: str
