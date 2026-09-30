import os
import sys
import subprocess


def get_default_journal_dir() -> str:
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
    else:
        raise NotImplementedError(f"Your os ({sys.platform}) is not supported")


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
