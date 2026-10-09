from typing import Literal

from pydantic import BaseModel, Field

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Faction(BaseModel):
    Name: str
    FactionState: str


class Economy(BaseModel):
    Name: str
    Proportion: float


class Pads(BaseModel):
    Small: int
    Medium: int
    Large: int


class Docked(JournalEntryBase):
    event: Literal[JournalEntryKind.Docked] = JournalEntryKind.Docked
    StationName: str
    MarketID: int
    SystemAddress: int
    StationType: str
    StarSystem: str
    StationFaction: Faction
    StationAllegiance: str | None = Field(default=None)
    StationEconomy: str
    StationEconomies: list[Economy]
    StationGovernment: str
    DistFromStarLS: float
    StationServices: list[str]
    LandingPads: Pads
    StationState: str | None = Field(default=None)
