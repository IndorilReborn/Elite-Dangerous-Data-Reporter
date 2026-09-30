import os
from queue import Queue

from pydantic import BaseModel, ValidationError
from sqlmodel import Session, func, select

from eddr.db import JournalFile, engine
from eddr.journal_schemas import RawJournalEntry
from eddr.journal_schemas.base import JournalEntryKind


class JournalEntry(BaseModel):
    entry: RawJournalEntry
    fid: str
    active: bool


class JournalReader:
    def __init__(self):
        self.unprocessed_journal_entries: Queue[JournalEntry] = Queue()

    def active_journals(self) -> list[JournalFile]:
        with Session(engine) as db:
            stmt = select(JournalFile).where(JournalFile.active == True)
            return list(db.exec(stmt).all())

    def active_fids(self) -> list[str]:
        with Session(engine) as db:
            row_number = (
                func.row_number()
                .over(
                    partition_by=JournalFile.fid,
                    order_by=JournalFile.filename.desc(),  # type: ignore
                )
                .label("rn")
            )

            subquery = select(
                JournalFile.fid, JournalFile.active, row_number
            ).subquery()

            query = (
                select(subquery.c.fid)
                .where(subquery.c.rn == 1)
                .where(subquery.c.active == True)
            )

            rows = db.exec(query).all()
            return list(rows)

    def update_journal_file(self, journal_file: str):
        with Session(engine) as db:
            db_journal_file = db.get(JournalFile, journal_file)

            journal_file_size = os.path.getsize(journal_file)

            # We've already read this journal somewhat
            if db_journal_file:
                if db_journal_file.last_read_offest < journal_file_size:
                    with open(journal_file, encoding="utf-8") as file:
                        file.seek(db_journal_file.last_read_offest)
                        lines = file.readlines()
                        journal_entries = self._read_events(lines)

                        is_active = self._get_is_journal_active(journal_entries)
                        db_journal_file.active = is_active

                        for journal_entry in journal_entries:
                            self.unprocessed_journal_entries.put_nowait(
                                JournalEntry(
                                    entry=journal_entry,
                                    fid=db_journal_file.fid,
                                    active=is_active,
                                )
                            )

                        db_journal_file.last_read_offest = file.tell()
                    db.add(db_journal_file)
                    db.commit()
                return

            with open(journal_file, encoding="utf-8") as file:
                lines = file.readlines()
                journal_entries = self._read_events(lines)

                fid = self._get_fid_from_journal_entries(journal_entries)
                if not fid:
                    return

                is_active = self._get_is_journal_active(journal_entries)

                db_journal_file = JournalFile(
                    filename=journal_file,
                    active=is_active,
                    fid=fid,
                    last_read_offest=file.tell(),
                )
                db.add(db_journal_file)
                db.commit()

                for journal_entry in journal_entries:
                    self.unprocessed_journal_entries.put_nowait(
                        JournalEntry(entry=journal_entry, fid=fid, active=is_active)
                    )

    @staticmethod
    def _read_events(raw_journal_lines: list[str]) -> list[RawJournalEntry]:
        journal_entries = []
        for line in raw_journal_lines:
            try:
                journal_entry = RawJournalEntry.model_validate_json(line.strip())
                journal_entries.append(journal_entry)
            except ValidationError:
                pass
                # journal_entry = json.loads(line)
                # print(f"WARNING: could not read event: {journal_entry['event']}")
        return journal_entries

    @staticmethod
    def _get_fid_from_journal_entries(
        journal_entries: list[RawJournalEntry],
    ) -> str | None:
        for journal_entry in journal_entries:
            if journal_entry.root.event == JournalEntryKind.Commander:
                return journal_entry.root.FID

    @staticmethod
    def _get_is_journal_active(journal_entries: list[RawJournalEntry]) -> bool:
        return (
            len(journal_entries) == 0
            or journal_entries[-1].root.event != JournalEntryKind.Shutdown
        )
