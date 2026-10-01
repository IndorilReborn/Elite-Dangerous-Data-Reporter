import os
import threading
import urllib.parse
from datetime import UTC, datetime
from queue import Empty
from typing import cast

from sqlmodel import Session, col, select
from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from eddr.controller.overview import OverviewController
from eddr.db import (
    Carrier,
    CMDRLocation,
    CMDRLocationCarrier,
    CMDRLocationStation,
    CMDRLocationSuperCruise,
    CMDRLocationUnknown,
    CMDRStatus,
    engine,
)
from eddr.journal_reader import JournalEntry, JournalReader
from eddr.journal_schemas.base import JournalEntryKind
from eddr.journal_schemas.carrier_jump import CarrierJump
from eddr.journal_schemas.fsd_jump import FSDJump
from eddr.journal_schemas.location import Location
from eddr.models import Model
from eddr.utils import open_file
from eddr.view import View


class JournalEventHandler(FileSystemEventHandler):
    def __init__(self, controller: "Controller"):
        self.controller = controller

    def on_modified(
        self,
        event: DirModifiedEvent
        | FileModifiedEvent
        | DirCreatedEvent
        | FileCreatedEvent,
    ) -> None:
        assert isinstance(event.src_path, str)
        if event.is_directory:
            return
        if not event.src_path.endswith(".log"):
            return
        self.controller._schedule_journal_update(event.src_path)

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        self.on_modified(event)


class Controller:
    def __init__(self, journal_dirs: list[str], model: Model, view: View):
        self.journal_dirs = journal_dirs
        self.journal_reader = JournalReader()

        self.model = model
        self.view = view

        self.overview = OverviewController(self)

        self.update_pending_for_journal: dict[str, bool] = {}

        self._observer = Observer()
        self._observer.daemon = True
        self._observer.start()

        threading.Thread(target=self._warm_up_journals, daemon=True).start()

    def _warm_up_journals(self):
        handler = JournalEventHandler(self)

        journal_files = []
        for journal_dir in self.journal_dirs:
            self._observer.schedule(handler, journal_dir, recursive=False)

            files = os.listdir(journal_dir)
            files = sorted(files)
            journal_files += [
                os.path.join(journal_dir, i) for i in files if i.endswith(".log")
            ]

        print(f"Starting to read journals... {datetime.now(UTC)}")
        for journal_file in journal_files:
            self.journal_reader.update_journal_file(journal_file)
        print(f"Journals processed {datetime.now(UTC)}")

        print(f"Handling startup messages... {datetime.now(UTC)}")
        # Just catch up before we start handling new stuff
        self._process_journal_messages()
        print(f"Finished catching up {datetime.now(UTC)}")
        self.update_active_journals()
        self.view.set_state("overview")

    def _schedule_journal_update(self, journal_path: str):
        self.view.add_callback(self._schedule_debounced_journal_update, journal_path)

    def _schedule_debounced_journal_update(self, journal_path: str):
        if self.update_pending_for_journal.get(journal_path, False):
            return
        self.update_pending_for_journal[journal_path] = True
        self.view.add_callback(self._update_journal, journal_path)

    def _update_journal(self, journal_path: str):
        self.journal_reader.update_journal_file(journal_path)
        self._process_journal_messages()
        self.update_active_journals()
        self.update_pending_for_journal[journal_path] = False

    def _process_journal_messages(self):
        while True:
            try:
                msg = self.journal_reader.unprocessed_journal_entries.get_nowait()
            except Empty:
                break
            self._process_journal_msg(msg)

    def _process_journal_msg(self, msg: JournalEntry):
        with Session(engine) as db:
            if msg.entry.root.event == JournalEntryKind.CarrierStats:
                carrier_info = db.get(Carrier, msg.entry.root.CarrierID)
                if not carrier_info:
                    carrier_info = Carrier(
                        market_id=msg.entry.root.CarrierID,
                        callsign=msg.entry.root.Callsign,
                        name=msg.entry.root.Name,
                    )
                else:
                    carrier_info.name = msg.entry.root.Name
                db.add(carrier_info)
                db.commit()
                return

            if not msg.active:
                return

            cmdr = db.get(CMDRStatus, msg.fid)
            is_selected_cmdr = (
                self.get_name_from_fid(msg.fid) == self.model.selected_cmdr_name.get()
            )
            cmdr_updated = False

            if not cmdr:
                cmdr = CMDRStatus(
                    fid=msg.fid,
                    name="Unknown CMDR",
                    location=CMDRLocation(root=CMDRLocationUnknown()),
                    last_updated=msg.entry.root.timestamp,
                )

            if msg.entry.root.event == JournalEntryKind.Commander:
                cmdr.name = msg.entry.root.Name
                cmdr_updated = True
            elif msg.entry.root.event == JournalEntryKind.Location:
                self._process_location(cmdr, msg.fid, msg.entry.root)
                cmdr_updated = True
            elif msg.entry.root.event == JournalEntryKind.FSDJump:
                self._process_fsd_or_carrier_jump(cmdr, msg.fid, msg.entry.root)
                cmdr_updated = True
            elif (
                msg.entry.root.event == JournalEntryKind.SuperCruiseEntry
                or msg.entry.root.event == JournalEntryKind.Undocked
            ):
                assert not isinstance(cmdr.location.root, CMDRLocationUnknown)
                cmdr.location = CMDRLocation(
                    root=CMDRLocationSuperCruise(
                        system_name=cmdr.location.root.system_name,
                        system_address=cmdr.location.root.system_address,
                        system_coords=cmdr.location.root.system_coords,
                    )
                )
                cmdr_updated = True
            elif msg.entry.root.event == JournalEntryKind.SuperCruiseExit:
                pass
            elif msg.entry.root.event == JournalEntryKind.Docked:
                assert not isinstance(cmdr.location.root, CMDRLocationUnknown)
                if msg.entry.root.StationType == "FleetCarrier":
                    cmdr.location = CMDRLocation(
                        root=CMDRLocationCarrier(
                            system_name=cmdr.location.root.system_name,
                            system_address=cmdr.location.root.system_address,
                            system_coords=cmdr.location.root.system_coords,
                            callsign=cast(str, msg.entry.root.StationName),
                            market_id=cast(int, msg.entry.root.MarketID),
                        )
                    )
                else:
                    cmdr.location = CMDRLocation(
                        root=CMDRLocationStation(
                            system_name=cmdr.location.root.system_name,
                            system_address=cmdr.location.root.system_address,
                            system_coords=cmdr.location.root.system_coords,
                            name=cast(str, msg.entry.root.StationName),
                            market_id=cast(int, msg.entry.root.MarketID),
                        )
                    )
                cmdr_updated = True

            db.add(cmdr)
            db.commit()

            if cmdr_updated and is_selected_cmdr:
                self.overview._selected_cmdr_updated()

    def _process_fsd_or_carrier_jump(
        self, cmdr: CMDRStatus, fid: str, msg: FSDJump | CarrierJump
    ):
        cmdr.location = CMDRLocation(
            root=CMDRLocationSuperCruise(
                system_name=msg.StarSystem,
                system_address=msg.SystemAddress,
                system_coords=msg.StarPos,
            )
        )

    def _process_location(self, cmdr: CMDRStatus, fid: str, msg: Location):
        if msg.Docked and msg.StationType == "FleetCarrier":
            cmdr.location = CMDRLocation(
                root=CMDRLocationCarrier(
                    system_name=msg.StarSystem,
                    system_address=msg.SystemAddress,
                    system_coords=msg.StarPos,
                    callsign=cast(str, msg.StationName),
                    market_id=cast(int, msg.MarketID),
                )
            )
        elif msg.Docked and msg.StationType == "Station":
            cmdr.location = CMDRLocation(
                root=CMDRLocationStation(
                    system_name=msg.StarSystem,
                    system_address=msg.SystemAddress,
                    system_coords=msg.StarPos,
                    name=cast(str, msg.StationName),
                    market_id=cast(int, msg.MarketID),
                )
            )
        else:
            cmdr.location = CMDRLocation(
                root=CMDRLocationSuperCruise(
                    system_name=msg.StarSystem,
                    system_address=msg.SystemAddress,
                    system_coords=msg.StarPos,
                )
            )

    def get_name_from_fid(self, fid: str) -> str | None:
        with Session(engine) as db:
            name = db.exec(
                select(CMDRStatus.name).where(CMDRStatus.fid == fid).limit(1)
            ).first()
            return name

    def update_active_journals(self):
        active_fids = self.journal_reader.active_fids()
        with Session(engine) as db:
            names = db.exec(
                select(CMDRStatus.name).where(col(CMDRStatus.fid).in_(active_fids))
            ).all()

            self.view.overview.cmdr_selector_combobox.configure(values=list(names))

            if len(names) == 0:
                self.view.model.selected_cmdr_name.set("Waiting for game...")
                return
            if len(names) == 1:
                self.view.model.selected_cmdr_name.set(names[0])
                return
            if self.view.model.selected_cmdr_name.get() not in names:
                self.view.model.selected_cmdr_name.set("Select a CMDR...")

    def open_system_on_inara(self, system_name: str):
        params = urllib.parse.urlencode({"search": system_name})
        open_file(f"https://inara.cz/elite/starsystem/?{params}")
