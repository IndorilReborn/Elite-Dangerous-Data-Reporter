from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Undocked(JournalEntryBase):
    event: Literal[JournalEntryKind.Undocked] = JournalEntryKind.Undocked
