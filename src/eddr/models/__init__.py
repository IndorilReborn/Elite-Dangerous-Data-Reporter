from tkinter import StringVar

from pydantic import BaseModel
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
        self.route = RouteModel(self)

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


class RouteSystem(BaseModel):
    completed: bool
    system_name: str
    boost: bool
    refuel: bool


class CMDRRoute(BaseModel):
    destination: str
    progress: int
    route: list[RouteSystem] = []


class RouteModel:
    def __init__(self, parent: Model):
        self._parent = parent
        self.destination = StringVar(value="")
        self.destination_suggestions: dict[str, int] = {}
        self.routes: dict[str, CMDRRoute] = {}

    @property
    def current_route(self) -> CMDRRoute | None:
        cmdr = self._parent.selected_cmdr
        if not cmdr:
            return None

        fid = cmdr.fid

        return self.routes.get(fid, None)
