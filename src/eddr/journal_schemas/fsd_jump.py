from typing import Literal

from pydantic import BaseModel, Field

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class ControllingFaction(BaseModel):
    Name: str
    FactionState: str


class ActiveState(BaseModel):
    State: str


class Faction(BaseModel):
    Name: str
    FactionState: str
    Government: str
    Influence: float
    Allegiance: str
    Happiness: str
    ActiveStates: list[ActiveState] | None = Field(default=None)


class ConflictFaction(BaseModel):
    Name: str
    Stake: str
    WonDays: int


class Conflict(BaseModel):
    WarType: str
    Status: str
    Faction1: ConflictFaction
    Faction2: ConflictFaction


class FSDJump(JournalEntryBase):
    event: Literal[JournalEntryKind.FSDJump] = JournalEntryKind.FSDJump
    StarSystem: str
    SystemAddress: int
    StarPos: tuple[float, float, float]
    Body: str
    SystemFaction: ControllingFaction
    SystemAllegiance: str
    SystemEconomy: str
    SystemSecondEconomy: str
    SystemGovernment: str
    SystemSecurity: str
    Population: int
    Factions: list[Faction]
