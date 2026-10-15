import json
import os
import threading
import time
from typing import TYPE_CHECKING

import requests

from eddr.db import CMDRLocationKind
from eddr.journal_reader import JournalEntry
from eddr.journal_schemas.base import JournalEntryKind
from eddr.models import CMDRRoute, RouteSystem
from eddr.utils import get_resource_path

if TYPE_CHECKING:
    from eddr.controller import Controller


class RouteController:
    def __init__(self, parent: "Controller"):
        self.parent = parent
        self.model = self.parent.model.route
        self.view = self.parent.view.route_view

        self.view.destination_input.configure(
            on_debounced_keypress=self._get_destination_suggestions
        )
        self.view.button.configure(command=self._get_route)

        self._fsd_info = {}
        with open(get_resource_path(os.path.join("data", "fsds.json"))) as f:
            data = json.load(f)
            self._fsd_info = {entry["fdname"].lower(): entry for entry in data}

    def process_journal_event(self, event: JournalEntry):
        if self.parent.warm_up:
            return

        if (
            event.entry.root.event == JournalEntryKind.FSDJump
            or event.entry.root.event == JournalEntryKind.CarrierJump
        ):
            new_system = event.entry.root.StarSystem
            self._update_route_progress(new_system)
        elif event.entry.root.event == JournalEntryKind.Music:
            if event.entry.root.MusicTrack == "GalaxyMap":
                self._copy_next_route_system()

    def on_cmdr_selected(self):
        route = self.model.current_route

        self.view.results.pack_forget()
        self.view.refuel.pack_forget()
        self.view.neutron.pack_forget()

        if route:
            self.view.destination_input.configure(value=route.destination)
            self.view.results.pack(side="top", fill="x", expand=False)
            self.view.next_system.configure(
                text=route.route[route.progress + 1].system_name
            )
            if route.route[route.progress].refuel:
                self.view.refuel.pack(side="top", fill="x", padx=5, pady=5)
            if route.route[route.progress].boost:
                self.view.neutron.pack(side="top", fill="x", padx=5, pady=5)

    def _copy_next_route_system(self):
        if not self.model.current_route:
            return

        next_system = self.model.current_route.route[
            self.model.current_route.progress + 1
        ].system_name
        self.view.parent.copy_to_clipboard(next_system)

    def _update_route_progress(self, current_system_name: str):
        if not self.model.current_route:
            return

        if (
            self.model.current_route.route[
                self.model.current_route.progress + 1
            ].system_name
            != current_system_name
        ):
            return

        self.model.current_route.progress += 1

        if self.model.current_route.progress == len(self.model.current_route.route) - 1:
            self.view.results.pack_forget()
            self.view.refuel.pack_forget()
            self.view.neutron.pack_forget()
            cmdr = self.model._parent.selected_cmdr
            assert cmdr is not None
            del self.model.routes[cmdr.fid]
            return

        self.view.neutron.pack_forget()
        self.view.refuel.pack_forget()

        self.view.jump_counter.configure(
            text=f"{self.model.current_route.progress}/{len(self.model.current_route.route) - 1}"
        )
        self.view.next_system.configure(
            text=f"{self.model.current_route.route[self.model.current_route.progress + 1].system_name}"
        )

        if self.model.current_route.route[self.model.current_route.progress].refuel:
            self.view.refuel.pack(side="top", fill="x", expand=False, padx=5, pady=5)

        if self.model.current_route.route[self.model.current_route.progress].boost:
            self.view.neutron.pack(side="top", fill="x", expand=False, padx=5, pady=5)

    def _get_route(self):
        destination = self.model.destination.get()
        destination_id = self.model.destination_suggestions[destination.lower()]

        cmdr = self.parent.model.selected_cmdr
        if not cmdr:
            return
        assert cmdr.location.root.location_type != CMDRLocationKind.Unknown
        start_id = cmdr.location.root.system_address

        self.view.destination_input.configure(state="disabled")
        self.view.button.configure(state="disabled")
        self.view.progress.pack(
            after=self.view.button, side="top", fill="x", expand=False, padx=5, pady=5
        )
        self.view.results.pack_forget()
        self.view.refuel.pack_forget()
        self.view.neutron.pack_forget()

        def route():
            fsd_module = next(
                module
                for module in cmdr.current_ship_slef.Modules
                if module.Slot == "FrameShiftDrive"
            )
            fsd_info = self._fsd_info[fsd_module.Item.lower()]

            fsd_optimal_mass = fsd_info["fsdoptmass"]
            fsd_max_fuel = fsd_info["maxfuel"]
            fsd_fuel_multiplier = fsd_info["fuelmul"]
            fsd_fuel_power = fsd_info["fuelpower"]
            fsd_supercharge_multiplier = fsd_info.get("charmul", 4)

            if fsd_engineering := fsd_module.Engineering:
                optimalmass = [
                    modifier
                    for modifier in fsd_engineering.Modifiers
                    if modifier.Label == "FSDOptimalMass"
                ]
                if optimalmass:
                    fsd_optimal_mass = optimalmass[0].Value

            route_params = {
                "source": str(start_id),
                "destination": str(destination_id),
                "is_supercharged": "0",
                "use_supercharge": "1",
                "use_injections": "0",
                "use_injections_when_required": "0",
                "exclude_secondary": "0",
                "refuel_every_scoopable": "0",
                "fuel_power": str(fsd_fuel_power),
                "fuel_multiplier": str(fsd_fuel_multiplier),
                "optimal_mass": str(fsd_optimal_mass),
                "base_mass": str(
                    cmdr.current_ship_slef.UnladenMass
                    + cmdr.current_ship_slef.FuelCapacity.Reserve
                ),
                "tank_size": str(cmdr.current_ship_slef.FuelCapacity.Main),
                "internal_tank_size": str(cmdr.current_ship_slef.FuelCapacity.Reserve),
                "reserve_size": "0",
                "max_fuel_per_jump": str(fsd_max_fuel),
                "range_boost": "10.5",
                "ship_build": cmdr.current_ship_slef.model_dump_json(),
                "max_time": "60",
                "cargo": "0",
                "algorithm": "optimistic",
                "supercharge_mutliplier": fsd_supercharge_multiplier,
                "injection_multiplier": "2",
            }

            res = requests.post(
                "https://www.spansh.co.uk/api/generic/route", data=route_params
            )
            if res.status_code != 200 and res.status_code != 202:
                raise Exception(f"Spansh didn't like that: {res.text}")
            res = res.json()
            route_identifier = res["job"]

            while True:
                res = requests.get(
                    f"https://www.spansh.co.uk/api/results/{route_identifier}"
                )
                if res.status_code == 202:
                    time.sleep(5)
                    continue
                if res.status_code != 200:
                    raise Exception(f"Spansh didn't like that: {res.text}")
                break

            res = res.json()
            route = res["result"]["jumps"]
            for entry in route:
                entry["completed"] = False
            route[0]["completed"] = True

            self.model.routes[cmdr.fid] = CMDRRoute(
                progress=0,
                route=[
                    RouteSystem(
                        completed=entry["completed"],
                        system_name=entry["name"],
                        boost=entry["has_neutron"],
                        refuel=entry["must_refuel"],
                    )
                    for entry in route
                ],
                destination=destination,
            )

            def update_ui():
                self.view.progress.pack_forget()
                self.view.destination_input.configure(state="normal")
                self.view.button.configure(state="normal")
                self.view.results.pack(side="top", fill="x", expand=False)
                self.view.jump_counter.configure(text=f"0/{len(route) - 1}")
                self.view.next_system.configure(text=f"{route[1]['name']}")

                if route[0]["must_refuel"]:
                    self.view.refuel.pack(
                        side="top", fill="x", expand=False, padx=5, pady=5
                    )

                if route[0]["has_neutron"]:
                    self.view.neutron.pack(
                        side="top", fill="x", expand=False, padx=5, pady=5
                    )

            self.parent.view.add_callback(update_ui)

        threading.Thread(target=route, daemon=True).start()

    def _get_destination_suggestions(self) -> bool:
        search_phrase = self.model.destination.get()

        if len(search_phrase) < 3:
            return False

        if any(
            search_phrase.lower() == key for key in self.model.destination_suggestions
        ):
            self.view.button.configure(state="normal")
            return False

        search_string = {
            "filters": {"name": {"value": f"{search_phrase}"}},
            "sort": [],
            "size": 5,
            "page": 0,
        }

        def fetch():
            res = requests.post(
                "https://www.spansh.co.uk/api/systems/search/save",
                data=json.dumps(search_string),
            )
            if res.status_code != 200:
                raise Exception(f"Spansh didn't like that: {res.text}")

            res = res.json()
            ref_string = res["search_reference"]

            res = requests.get(
                f"https://www.spansh.co.uk/api/systems/search/recall/{ref_string}"
            )

            if res.status_code != 200:
                raise Exception(f"Spansh didn't like that: {res.text}")

            res = res.json()["results"]

            def update_ui():
                self.model.destination_suggestions = {
                    entry["name"].lower(): entry["id64"] for entry in res
                }
                self.view.destination_input.configure(
                    values=[entry["name"] for entry in res]
                )
                self.view.destination_input.event_generate("<Down>")

            self.parent.view.add_callback(update_ui)

        threading.Thread(target=fetch, daemon=True).start()
        return False
