from typing import Annotated

from pydantic import Field, RootModel

from eddr.journal_schemas.carrier_jump import CarrierJump
from eddr.journal_schemas.carrier_stats import CarrierStats
from eddr.journal_schemas.commander import Commander
from eddr.journal_schemas.docked import Docked
from eddr.journal_schemas.fsd_jump import FSDJump
from eddr.journal_schemas.heading import Heading
from eddr.journal_schemas.load_game import LoadGame
from eddr.journal_schemas.loadout import Loadout
from eddr.journal_schemas.location import Location
from eddr.journal_schemas.market import Market
from eddr.journal_schemas.music import MusicEntry
from eddr.journal_schemas.shutdown import Shutdown
from eddr.journal_schemas.supercruise_entry import SuperCruiseEntry
from eddr.journal_schemas.supercruise_exit import SuperCruiseExit
from eddr.journal_schemas.undocked import Undocked

VALID_JOURNAL_ENTRIES = [
    Heading,
    Commander,
    Shutdown,
    Location,
    FSDJump,
    CarrierJump,
    SuperCruiseEntry,
    SuperCruiseExit,
    Docked,
    Undocked,
    CarrierStats,
    Loadout,
    Market,
    LoadGame,
    MusicEntry,
]

RawJournalEntry = RootModel[
    Annotated[
        Heading
        | Commander
        | Shutdown
        | Location
        | FSDJump
        | CarrierJump
        | SuperCruiseEntry
        | SuperCruiseExit
        | Docked
        | Undocked
        | CarrierStats
        | Loadout
        | Market
        | LoadGame
        | MusicEntry,
        Field(discriminator="event"),
    ]
]
