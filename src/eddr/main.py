import os
import sys
import tkinter as tk
from argparse import ArgumentParser

import sv_ttk
from alembic import command
from alembic.config import Config
from sqlmodel import SQLModel

from eddr.constants import WINDOW_SIZE
from eddr.controller import Controller
from eddr.db import db_path, engine
from eddr.models import Model
from eddr.utils import get_default_journal_dir, get_resource_path
from eddr.view import View


def main() -> None:
    print("EDDR is starting...")

    migrate_database()
    SQLModel.metadata.create_all(engine)

    root = tk.Tk()
    sv_ttk.use_dark_theme()
    root.title("Elite Dangerous Data Reporter")
    root.geometry(WINDOW_SIZE)

    journal_dirs = get_journal_paths()

    model = Model()
    view = View(root, model)
    Controller(journal_dirs, model, view)
    root.mainloop()


def migrate_database():
    print("Running DB migrations...")
    alembic_cfg = Config(get_resource_path("alembic.ini"))
    alembic_cfg.set_main_option("script_location", "src/eddr/alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(alembic_cfg, "head")
    print("Done")


def get_journal_paths() -> list[str]:
    parser = ArgumentParser()
    parser.add_argument(
        "-p",
        "--paths",
        nargs="+",
        dest="paths",
        default=None,
        help="Journal paths: override journal paths(s)",
    )
    args = parser.parse_args()

    env_journal_paths = os.getenv("EDDR_JOURNAL_PATHS")
    if args.paths:
        journal_paths = args.paths
    elif env_journal_paths is not None and env_journal_paths.strip():
        journal_paths = [
            path.strip() for path in env_journal_paths.split(";") if path.strip()
        ]
        if not journal_paths:
            journal_paths = None
    else:
        journal_paths = [get_default_journal_dir()]
    assert journal_paths is not None, (
        f"No default journal path for platform {sys.platform}, please specify one with --paths or the EDDR_JOURNAL_PATHS env var"
    )
    for journal_path in journal_paths:
        assert os.path.exists(journal_path), (
            f"Journal path {journal_path} does not exist, please specify one with --paths or the EDDR_JOURNAL_PATHS env var"
        )

    return journal_paths


if __name__ == "__main__":
    main()
