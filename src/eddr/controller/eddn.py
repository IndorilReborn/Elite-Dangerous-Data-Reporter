import os
import threading
from queue import Queue
from typing import TYPE_CHECKING, Any

import requests
from sqlmodel import Session

from eddr.db import CMDRLocationKind, CMDRStatus, engine
from eddr.journal_reader import JournalEntry
from eddr.journal_schemas.base import JournalEntryKind
from eddr.journal_schemas.docked import Docked
from eddr.journal_schemas.fsd_jump import FSDJump
from eddr.journal_schemas.market import Market, MarketFileEntry
from eddr.utils import get_resource_path

if TYPE_CHECKING:
    from eddr.controller import Controller


class EDDNController:
    def __init__(self, parent: "Controller"):
        self.parent = parent

        with open(get_resource_path("VERSION")) as f:
            self.version = f.read()

        self.eddn_queue: Queue[dict[str, Any]] = Queue()

        self.parent.view.overview.silent_on.trace_add(
            "write", lambda *args: self._update_silent_mode()
        )

        threading.Thread(target=self._process_eddn_queue, daemon=True).start()

    def process_entry(self, msg: JournalEntry):
        # We do not upload anything from before we were running
        if self.parent.warm_up:
            return

        with Session(engine) as db:
            cmdr = db.get(CMDRStatus, msg.fid)

        if not cmdr:
            return

        if cmdr.silent:
            return

        if msg.entry.root.event == JournalEntryKind.Market:
            journal_dir = os.path.dirname(msg.journal_file)
            market_file = os.path.join(journal_dir, "market.json")
            market_entry = None
            with open(market_file, "r") as f:
                market_entry = MarketFileEntry.model_validate_json(f.read())
            if market_entry is None:
                return
            if market_entry.MarketID != msg.entry.root.MarketID:
                return

            self._send_market(cmdr, msg.entry.root, market_entry)
        if msg.entry.root.event == JournalEntryKind.FSDJump:
            self._send_fsd_jump_to_eddn(cmdr, msg.entry.root)
        if msg.entry.root.event == JournalEntryKind.Docked:
            self._send_docked_to_eddn(cmdr, msg.entry.root)

    def _send_docked_to_eddn(self, cmdr: CMDRStatus, journal_msg: Docked):
        assert cmdr.location.root.location_type != CMDRLocationKind.Unknown
        if journal_msg.StarSystem != cmdr.location.root.system_name:
            return
        if journal_msg.SystemAddress != cmdr.location.root.system_address:
            return

        msg_dict = journal_msg.model_dump()
        msg_dict["timestamp"] = msg_dict["timestamp"].isoformat()
        msg_dict["StarPos"] = list(cmdr.location.root.system_coords)
        msg_dict["horizons"] = cmdr.horizons
        msg_dict["odyssey"] = cmdr.odyssey

        docked_msg = {
            "$schemaRef": "https://eddn.edcd.io/schemas/journal/1",
            "header": {
                "uploaderID": cmdr.name,
                "gameversion": cmdr.gameversion,
                "gamebuild": cmdr.gamebuild,
                "softwareName": "Elite Dangerous Data Reporter",
                "softwareVersion": self.version,
            },
            "message": msg_dict,
        }

        self.eddn_queue.put_nowait(docked_msg)

    def _send_fsd_jump_to_eddn(self, cmdr: CMDRStatus, journal_msg: FSDJump):
        msg_dict = journal_msg.model_dump()
        msg_dict["timestamp"] = msg_dict["timestamp"].isoformat()
        msg_dict["horizons"] = cmdr.horizons
        msg_dict["odyssey"] = cmdr.odyssey

        jump_msg = {
            "$schemaRef": "https://eddn.edcd.io/schemas/journal/1",
            "header": {
                "uploaderID": cmdr.name,
                "gameversion": cmdr.gameversion,
                "gamebuild": cmdr.gamebuild,
                "softwareName": "Elite Dangerous Data Reporter",
                "softwareVersion": self.version,
            },
            "message": msg_dict,
        }

        self.eddn_queue.put_nowait(jump_msg)

    def _send_market(
        self, cmdr: CMDRStatus, journal_msg: Market, market_info: MarketFileEntry
    ):
        commodities = []
        for commodity in market_info.Items:
            if commodity.Category == "$MARKET_category_non_marketable":
                continue
            if (commodity.Legality or "") != "":
                continue

            status_flags = []
            if commodity.Producer is True:
                status_flags.append("Producer")
            if commodity.Consumer is True:
                status_flags.append("Consumer")
            if commodity.Rare is True:
                status_flags.append("Rare")

            new_commodity = {
                "name": commodity.Name.removeprefix("$").removesuffix("_name;"),
                "meanPrice": commodity.MeanPrice,
                "buyPrice": commodity.BuyPrice,
                "stock": commodity.Stock,
                "stockBracket": commodity.StockBracket,
                "sellPrice": commodity.SellPrice,
                "demand": commodity.Demand,
                "demandBracket": commodity.DemandBracket,
            }

            if status_flags:
                new_commodity["statusFlags"] = status_flags
            commodities.append(new_commodity)

        market_msg = {
            "$schemaRef": "https://eddn.edcd.io/schemas/commodity/3",
            "header": {
                "uploaderID": cmdr.name,
                "gameversion": cmdr.gameversion,
                "gamebuild": cmdr.gamebuild,
                "softwareName": "Elite Dangerous Data Reporter",
                "softwareVersion": self.version,
            },
            "message": {
                "horizons": cmdr.horizons,
                "odyssey": cmdr.odyssey,
                "timestamp": journal_msg.timestamp.isoformat(),
                "systemName": journal_msg.StarSystem,
                "stationName": journal_msg.StationName,
                "stationType": journal_msg.StationType,
                "marketId": journal_msg.MarketID,
                "commodities": commodities,
            },
        }

        self.eddn_queue.put_nowait(market_msg)

    def _process_eddn_queue(self):
        while True:
            item = self.eddn_queue.get()
            try:
                self._send_to_eddn(item)
            except Exception as e:
                print(f"Unexpected error uploading to EDDN: {e!r}")

    def _send_to_eddn(self, item: dict):
        try:
            r = requests.post(
                "https://eddn.edcd.io:4430/upload/", json=item, timeout=10
            )
        except requests.RequestException as e:
            print(f"Error uploading to EDDN: {e!r}")
            return
        if r.status_code != 200:
            print(f"Error uploading to EDDN: {r.text}")

    def _update_silent_mode(self):
        new_setting = self.parent.view.overview.silent_on.get()
        selected_cmdr = self.parent.model.selected_cmdr
        if not selected_cmdr:
            return

        with Session(engine) as db:
            selected_cmdr.silent = new_setting
            db.add(selected_cmdr)
            db.commit()
