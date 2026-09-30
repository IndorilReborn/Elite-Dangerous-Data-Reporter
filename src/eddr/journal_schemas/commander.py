from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Commander(JournalEntryBase):
    event: Literal[JournalEntryKind.Commander] = JournalEntryKind.Commander
    Name: str
    FID: str
