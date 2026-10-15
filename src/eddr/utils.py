from functools import total_ordering
from itertools import zip_longest
import os
import re
import subprocess
import sys
from typing import cast

from pydantic import BaseModel, Field


def get_default_journal_dir() -> str | None:
    if sys.platform == "win32":
        user_path = os.environ.get("USERPROFILE")
        assert user_path is not None
        return os.path.join(
            user_path, "Saved Games", "Frontier Developments", "Elite Dangerous"
        )
    elif sys.platform == "linux":
        user_path = os.path.expanduser("~")
        return os.path.join(
            user_path,
            ".local",
            "share",
            "Steam",
            "steamapps",
            "compatdata",
            "359320",
            "pfx",
            "drive_c",
            "users",
            "steamuser",
            "Saved Games",
            "Frontier Developments",
            "Elite Dangerous",
        )
    return None


def get_app_dir() -> str:
    if sys.platform == "win32":
        user_path = os.environ.get("USERPROFILE")
        assert user_path is not None
        return os.path.join(
            user_path,
            "AppData",
            "Roaming",
            "YuiYukihira",
            "Elite Dangerous Data Reporter",
        )
    elif sys.platform == "linux" or sys.platform == "darwin":
        user_path = os.path.expanduser("~")
        return os.path.join(
            user_path, ".config", "YuiYukihira", "Elite Dangerous Date Reporter"
        )
    else:
        raise NotImplementedError(f"Your or ({sys.platform}) is not supported")


def get_resource_path(relative_path: str):
    base_path = getattr(
        sys,
        "_MEIPASS",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
    )
    return os.path.join(base_path, relative_path)


def open_file(filename: str):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


@total_ordering
class SemVer(BaseModel):
    major: int
    minor: int
    patch: int
    prerelease: str | None = Field(default=None)

    def __str__(self) -> str:
        base = f"v{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.prerelease) == (
            other.major,
            other.minor,
            other.patch,
            other.prerelease,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented

        self_ver = (self.major, self.minor, self.patch)
        other_ver = (other.major, other.minor, other.patch)

        if self_ver != other_ver:
            return self_ver < other_ver

        if self.prerelease is None:
            return False
        if other.prerelease is None:
            return True

        self_parts = self.prerelease.split(".")
        other_parts = other.prerelease.split(".")

        for self_part, other_part in zip_longest(self_parts, other_parts):
            if self_part is None:
                return True
            if other_part is None:
                return False
            if self_part == other_part:
                continue

            is_self_part_numeric = self_part.isdigit()
            is_other_part_numeric = other_part.isdigit()

            if is_self_part_numeric and is_other_part_numeric:
                return int(self_part) < int(other_part)
            if is_self_part_numeric != is_other_part_numeric:
                return is_self_part_numeric
            return self_part < other_part
        return False


def parse_version_str(version_str: str) -> SemVer | None:
    PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-(.+))?$")

    match = PATTERN.match(version_str)
    if not match:
        return None

    groups = match.groups()

    # Naive cast to int is fine because regex enforces digits only
    return SemVer(
        major=int(groups[0]),
        minor=int(groups[1]),
        patch=int(groups[2]),
        prerelease=None if len(groups) <= 3 else groups[3],
    )


with open(get_resource_path("VERSION")) as f:
    APP_VERSION = cast(SemVer, parse_version_str(f.read().strip()))
    assert APP_VERSION is not None, "Can not determine App Version"
