from typing import Literal

from pydantic import Field

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Heading(JournalEntryBase):
    event: Literal[JournalEntryKind.Heading] = JournalEntryKind.Heading
    part: int
    language: str
    Odyssey: bool | None = Field(default=None)
    gameversion: str
    build: str
