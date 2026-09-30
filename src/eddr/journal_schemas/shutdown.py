from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Shutdown(JournalEntryBase):
    event: Literal[JournalEntryKind.Shutdown] = JournalEntryKind.Shutdown
