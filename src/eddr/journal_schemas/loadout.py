from typing import Literal

from pydantic import BaseModel, Field

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class FuelCapacity(BaseModel):
    Main: float
    Reserve: float


class Modifier(BaseModel):
    Label: str
    Value: float | None = Field(default=None)
    ValueStr: str | None = Field(default=None)
    OriginalValue: float | None = Field(default=None)
    LessIsGood: int | None = Field(default=None)


class ModuleEngineering(BaseModel):
    EngineerID: int
    Engineer: str | None = Field(default=None)
    BlueprintID: int
    BlueprintName: str
    Level: int
    Quality: float
    ExperimentalEffect: str | None = Field(default=None)
    Modifiers: list[Modifier]


class Module(BaseModel):
    Slot: str
    Item: str
    On: bool
    Priority: int
    Health: float
    Value: int | None = Field(default=None)
    AmmoInClip: int | None = Field(default=None)
    AmmoInHopper: int | None = Field(default=None)
    Engineering: ModuleEngineering | None = Field(default=None)


class Loadout(JournalEntryBase):
    event: Literal[JournalEntryKind.Loadout] = JournalEntryKind.Loadout
    Ship: str
    ShipID: int
    ShipName: str
    ShipIdent: str
    HullValue: int | None = Field(default=None)
    ModulesValue: int | None = Field(default=None)
    UnladenMass: float
    CargoCapacity: int
    MaxJumpRange: float
    FuelCapacity: FuelCapacity
    Rebuy: int
    Modules: list[Module]
