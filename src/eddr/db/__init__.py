import enum
import os
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, RootModel, TypeAdapter
from sqlalchemy import Dialect
from sqlmodel import JSON, Field, SQLModel, TypeDecorator, create_engine

from eddr.journal_schemas.loadout import Loadout
from eddr.utils import get_app_dir

db_path = os.path.join(get_app_dir(), "eddr.db")
db_exists = os.path.exists(db_path)
if not os.path.exists(get_app_dir()):
    os.makedirs(get_app_dir())
engine = create_engine(f"sqlite:///{db_path}")


class PydanticJSON(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, pydantic_type: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pydantic_type = pydantic_type
        self.adapter = TypeAdapter(pydantic_type)

    def process_bind_param(self, value: Any | None, dialect: Dialect) -> Any:
        if value is None:
            return None

        return self.adapter.dump_python(value, mode="json")

    def process_result_value(self, value: Any | None, dialect: Dialect) -> Any | None:
        if value is None:
            return None

        return self.adapter.validate_python(value)


class JournalFile(SQLModel, table=True):
    filename: str = Field(primary_key=True)
    active: bool
    fid: str
    last_read_offest: int


class CMDRLocationKind(str, enum.Enum):
    SuperCruise = "SuperCruise"
    Station = "Station"
    Carrier = "Carrier"
    Unknown = "Unknown"


class CMDRLocationUnknown(BaseModel):
    location_type: Literal[CMDRLocationKind.Unknown] = CMDRLocationKind.Unknown


class CMDRLocationBase(BaseModel):
    system_name: str
    system_address: int
    system_coords: tuple[float, float, float]


class CMDRLocationSuperCruise(CMDRLocationBase):
    location_type: Literal[CMDRLocationKind.SuperCruise] = CMDRLocationKind.SuperCruise


class CMDRLocationStation(CMDRLocationBase):
    location_type: Literal[CMDRLocationKind.Station] = CMDRLocationKind.Station
    name: str
    market_id: int


class CMDRLocationCarrier(CMDRLocationBase):
    location_type: Literal[CMDRLocationKind.Carrier] = CMDRLocationKind.Carrier
    callsign: str
    market_id: int


CMDRLocation = RootModel[
    Annotated[
        CMDRLocationSuperCruise
        | CMDRLocationStation
        | CMDRLocationCarrier
        | CMDRLocationUnknown,
        Field(discriminator="location_type"),
    ]
]


class CMDRStatus(SQLModel, table=True):
    fid: str = Field(primary_key=True)
    name: str
    location: CMDRLocation = Field(sa_type=PydanticJSON(CMDRLocation))
    current_ship_slef: Loadout = Field(sa_type=PydanticJSON(Loadout))
    last_updated: datetime
    silent: bool = Field(default=False)
    gameversion: str
    gamebuild: str
    horizons: bool
    odyssey: bool


class Carrier(SQLModel, table=True):
    market_id: int = Field(primary_key=True)
    callsign: str
    name: str
