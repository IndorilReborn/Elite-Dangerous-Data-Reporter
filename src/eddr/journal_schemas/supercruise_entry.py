from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class SuperCruiseEntry(JournalEntryBase):
    event: Literal[JournalEntryKind.SuperCruiseEntry] = (
        JournalEntryKind.SuperCruiseEntry
    )
