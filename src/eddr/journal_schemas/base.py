import enum
from datetime import datetime

from pydantic import BaseModel


class JournalEntryKind(str, enum.Enum):
    Heading = "Fileheader"
    Commander = "Commander"
    Shutdown = "Shutdown"
    Location = "Location"
    FSDJump = "FSDJump"
    CarrierJump = "CarrierJump"
    SuperCruiseEntry = "SuperCruiseEntry"
    SuperCruiseExit = "SuperCruiseExit"
    Docked = "Docked"
    Undocked = "Undocked"
    CarrierStats = "CarrierStats"


class JournalEntryBase(BaseModel):
    timestamp: datetime
