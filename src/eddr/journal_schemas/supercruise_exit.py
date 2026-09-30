from typing import Literal

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class SuperCruiseExit(JournalEntryBase):
    event: Literal[JournalEntryKind.SuperCruiseExit] = JournalEntryKind.SuperCruiseExit
