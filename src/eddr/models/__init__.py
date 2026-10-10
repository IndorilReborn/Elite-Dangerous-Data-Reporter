from tkinter import StringVar

from sqlmodel import Session, select

from eddr.db import (
    Carrier,
    CMDRStatus,
    engine,
)


class Model:
    def __init__(self):
        self.selected_cmdr_name = StringVar(value="Waiting for game...")

        self.find = FindModel()

    @property
    def selected_cmdr(self) -> CMDRStatus | None:
        name = self.selected_cmdr_name.get()
        with Session(engine) as db:
            cmdr = db.exec(select(CMDRStatus).where(CMDRStatus.name == name)).first()
            return cmdr

    def get_carrier_name_by_market_id(self, market_id: int) -> str | None:
        with Session(engine) as db:
            carrier = db.exec(
                select(Carrier).where(Carrier.market_id == market_id)
            ).first()

            if not carrier:
                return None

            return f"{carrier.name} ({carrier.callsign})"


class FindModel:
    def __init__(self):
        self.lookup_type = StringVar(value="Refuel")
        self.results_system = StringVar(value="")
        self.results_location = StringVar(value="")
        self.results_type = ""
        self.last_search_params = ""
        self.results_location_ref = ""
