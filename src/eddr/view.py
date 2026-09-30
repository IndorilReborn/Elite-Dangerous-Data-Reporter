import tkinter as tk
import traceback
from collections.abc import Callable
from queue import Empty, Queue
from tkinter import StringVar, Tk, ttk
from typing import Any

from eddr.models import Model


class View:
    def __init__(self, root: Tk, model: Model):
        self.root = root
        self.model = model

        style = ttk.Style(self.root)
        # Remove the focus border around tabs
        style.layout(
            "Tab",
            [
                (
                    "Notebook.tab",
                    {
                        "sticky": "nswe",
                        "children": [
                            (
                                "Notebook.padding",
                                {
                                    "side": "top",
                                    "sticky": "nswe",
                                    "children": [
                                        (
                                            "Notebook.label",
                                            {"side": "top", "sticky": ""},
                                        )
                                    ],
                                },
                            )
                        ],
                    },
                )
            ],
        )

        self.sheet_colors = {
            "table_bg": "#1c1c1e",  # main window surface
            "header_bg": "#202021",  # secondary surface
            "header_fg": "#f3f3f5",  # light text
            "index_bg": "#202021",  # secondary surface
            "index_fg": "#C2C2C4",  # dim light text
            "top_left_bg": "#202021",  # secondary surface
            "cell_bg": "#1c1c1e",  # main window surface
            "cell_fg": "#f3f3f5",  # light text
            "selected_bg": "#0a84ff",  # Fluent accent blue
            "selected_fg": "#ffffff",  # white text on selection
        }

        style = ttk.Style()
        style.element_create(
            "Danger.TButton", "from", "sun-valley-dark", "Button.TButton"
        )
        style.layout("Danger.TButton", style.layout("Button.TButton"))
        style.configure("Danger.TButton", foreground="red")

        # Topbar
        self.top_bar = ttk.Frame(self.root)
        self.top_bar.pack(side="top", fill="x")

        # Clock
        self.clock_utc = ttk.Label(self.top_bar, width=8)
        self.clock_utc.pack(side="right", anchor="ne")

        self.tab_controller = ttk.Notebook(self.root)
        self.tab_controller.pack(expand=True, fill="both")

        self.overview = OverviewView(self)

        self._callbacks: Queue[
            tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]
        ] = Queue()
        self.root.after(0, self._drain_ui_callbacks)

    def add_callback(self, cb: Callable[..., Any], *args, **kwargs):
        self._callbacks.put_nowait((cb, args, kwargs))

    def copy_to_clipboard(self, text: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _drain_ui_callbacks(self):
        while True:
            try:
                callback, args, kwargs = self._callbacks.get_nowait()
            except Empty:
                break
            try:
                callback(*args, **kwargs)
            except Exception:
                print(f"Exception while running callback:\n{traceback.format_exc()}")
        self.root.after(50, self._drain_ui_callbacks)


class OverviewView:
    def __init__(self, parent: View):
        self.parent = parent

        self.tab = ttk.Frame(self.parent.tab_controller)
        self.parent.tab_controller.add(self.tab, text="Overview")

        self._cmdr_selector_frame = ttk.Frame(self.tab)
        self._cmdr_selector_frame.pack(
            side="top", fill="x", expand=False, padx=5, pady=5
        )
        self._cmdr_selector_label = ttk.Label(
            self._cmdr_selector_frame, text="Commander:"
        )
        self._cmdr_selector_label.pack(side="left", padx=(0, 5))
        self.cmdr_selector_combobox = ttk.Combobox(
            self._cmdr_selector_frame,
            textvariable=self.parent.model.selected_cmdr_name,
            values=[],
        )
        self.cmdr_selector_combobox.pack(side="left", fill="x", expand=False)

        self.system_name = StringVar(value="")
        self.system_frame = ttk.LabelFrame(self.tab, text="System")
        self.system_frame.pack(side="top", fill="x", expand=False, padx=5, pady=5)
        self._system_label = ttk.Label(self.system_frame, textvariable=self.system_name)
        self._system_label.pack(side="top", fill="x", expand=False, padx=5, pady=5)
        self.system_contextmenu = tk.Menu(self.parent.root, tearoff=0)
        self.system_frame.bind(
            "<Button-3>",
            lambda event: self.system_contextmenu.post(event.x_root, event.y_root),
        )
        self._system_label.bind(
            "<Button-3>",
            lambda event: self.system_contextmenu.post(event.x_root, event.y_root),
        )

        self.location_name = StringVar(value="")
        self.location_frame = ttk.LabelFrame(self.tab, text="System")
        self.location_frame.pack(side="top", fill="x", expand=False, padx=5, pady=5)
        self._location_label = ttk.Label(
            self.location_frame, textvariable=self.location_name
        )
        self._location_label.pack(side="top", fill="x", expand=False, padx=5, pady=5)
        self.location_contextmenu = tk.Menu(self.parent.root, tearoff=0)
        self.location_frame.bind(
            "<Button-3>",
            lambda event: self.location_contextmenu.post(event.x_root, event.y_root),
        )
        self._location_label.bind(
            "<Button-3>",
            lambda event: self.location_contextmenu.post(event.x_root, event.y_root),
        )
