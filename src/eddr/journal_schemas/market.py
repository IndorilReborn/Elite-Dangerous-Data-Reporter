from typing import Literal

from pydantic import BaseModel, Field

from eddr.journal_schemas.base import JournalEntryBase, JournalEntryKind


class Market(JournalEntryBase):
    event: Literal[JournalEntryKind.Market]
    MarketID: int
    StationName: str
    StationType: str
    CarrierDockingAccess: str | None = Field(default=None)
    StarSystem: str


class MarketItem(BaseModel):
    id: int
    Name: str
    Category: str
    BuyPrice: int
    SellPrice: int
    MeanPrice: int
    StockBracket: int
    DemandBracket: int
    Stock: int
    Demand: int
    Consumer: bool | None = Field(default=None)
    Producer: bool | None = Field(default=None)
    Rare: bool | None = Field(default=None)
    Legality: str | None = Field(default=None)


class MarketFileEntry(Market):
    Items: list[MarketItem]
