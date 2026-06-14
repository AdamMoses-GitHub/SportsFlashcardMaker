"""Desktop GUI for flashcard generation using tkinter."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .core import generate_flashcards_batch
from .teams import FLASHCARD_SETS, Team, format_output_filenames, APPROX_TEAM_COUNTS


class FlashcardGeneratorGUI:
    """Desktop GUI for generating flashcards."""

    DEFAULT_WIDTH = 760
    DEFAULT_HEIGHT = 500
    MIN_WIDTH = 620
    MIN_HEIGHT = 450
    MAX_FILENAME_PREVIEW_SETS = 6
    RATIO_META: dict[str, tuple[str, str]] = {
        "1x1": ("4x4 in", "square"),
        "3x2": ("6x4 in", "landscape"),
        "2x3": ("4x6 in", "portrait"),
        "5x4": ("5x4 in", "landscape"),
        "4x5": ("4x5 in", "portrait"),
        "7x5": ("7x5 in", "landscape"),
        "5x7": ("5x7 in", "portrait"),
        "8x10": ("8x10 in", "portrait"),
        "10x8": ("10x8 in", "landscape"),
    }
    SPLIT_COLOR_DISABLED_SET_CODES: frozenset[str] = frozenset(
        {
            "epl",
            "efl_championship",
            "efl_league_one",
            "efl_league_two",
            "nwsl",
            "la_liga",
            "bundesliga",
            "serie_a",
            "ligue_1",
        }
    )

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Flashcard Generator")
        self.root.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")
        self.root.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.root.resizable(True, True)

        self.output_path: str | None = None
        self.is_generating = False
        self._main_canvas: tk.Canvas | None = None
        self.generation_start_time: float | None = None

        self._build_menu()
        self._build_ui()
        self._setup_keyboard_shortcuts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._load_prefs()

    def _build_menu(self) -> None:
        """Build app menu bar."""
        menu_bar = tk.Menu(self.root)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Reset Window Size", command=self._reset_window_size)
        view_menu.add_command(label="Fit To Content", command=self._fit_to_content)
        menu_bar.add_cascade(label="View", menu=view_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="Clear Output Folder", command=self._on_clear_output)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        self.root.config(menu=menu_bar)

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Main container - holds scrollable area and buttons
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True)

        # Scrollable area container (expands with window)
        scroll_container = ttk.Frame(main_container)
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._main_canvas = canvas

        # Content frame with padding hosted inside scrollable canvas
        content_frame = ttk.Frame(canvas, padding=10)
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def _on_content_frame_configure(_event: tk.Event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event: tk.Event) -> None:
            # Expand content_frame to fill canvas width, but allow vertical scroll if needed
            canvas_width = event.width
            canvas_height = event.height
            content_frame.update_idletasks()
            content_height = content_frame.winfo_reqheight()
            
            # Set width to fill canvas, height to max of canvas or content
            window_height = max(canvas_height, content_height)
            canvas.itemconfigure(canvas_window, width=canvas_width, height=window_height)

        content_frame.bind("<Configure>", _on_content_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Title
        title = ttk.Label(content_frame, text="Sports Flashcard Maker", font=("Arial", 14, "bold"))
        title.pack(anchor="w")
        subtitle = ttk.Label(
            content_frame,
            text="Select sets, customize settings, then generate.",
            foreground="#555",
        )
        subtitle.pack(anchor="w", pady=(0, 8))

        # --- Main Tabs ---
        main_tabs = ttk.Notebook(content_frame)
        main_tabs.pack(fill="both", expand=True, pady=(0, 8))

        # ============ TAB 1: SETS ============
        sets_tab = ttk.Frame(main_tabs, padding=10)
        main_tabs.add(sets_tab, text="Leagues & Sets")

        toolbar = ttk.Frame(sets_tab)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Select All", command=self._select_all_sets).pack(side="left")
        ttk.Button(toolbar, text="Clear All", command=self._clear_set_selection).pack(side="left", padx=(8, 0))

        # Professional Leagues (non-English football)
        pro_frame = ttk.LabelFrame(sets_tab, text="Professional Leagues", padding=8)
        pro_frame.pack(fill="x", pady=(0, 8))

        self.set_vars: dict[str, tk.BooleanVar] = {}
        pro_sets = [
            "mlb",
            "nfl",
            "cfl",
            "nba",
            "nhl",
            "wnba",
            "mls",
            "nwsl",
            "ufl",
        ]
        default_selected: set[str] = set()

        for index, code in enumerate(pro_sets):
            row = index // 2
            col = index % 2
            team_set = FLASHCARD_SETS[code]
            var = tk.BooleanVar(value=code in default_selected)
            self.set_vars[code] = var

            count = len(team_set.teams) or APPROX_TEAM_COUNTS.get(code, 0)
            text = f"{team_set.display_name} ({count})" if count else team_set.display_name
            chk = ttk.Checkbutton(pro_frame, text=text, variable=var, command=self._update_info)
            chk.grid(row=row, column=col, sticky="w", padx=(0, 14), pady=2)

        # ── NCAA Div I College Football ──────────────────────────────────────
        ncaa_cfb_frame = ttk.LabelFrame(sets_tab, text="NCAA Div I College Football", padding=8)
        ncaa_cfb_frame.pack(fill="x", pady=(0, 0))

        # Combined "all conferences" option
        cfb_combined_row = ttk.Frame(ncaa_cfb_frame)
        cfb_combined_row.pack(fill="x", pady=(0, 6))
        _cfb_all_set = FLASHCARD_SETS["cfb_all"]
        cfb_all_var = tk.BooleanVar(value="cfb_all" in default_selected)
        self.set_vars["cfb_all"] = cfb_all_var
        cfb_all_count = len(_cfb_all_set.teams) or APPROX_TEAM_COUNTS.get("cfb_all", 0)
        ttk.Checkbutton(
            cfb_combined_row,
            text=f"{_cfb_all_set.display_name} ({cfb_all_count})" if cfb_all_count else _cfb_all_set.display_name,
            variable=cfb_all_var,
            command=self._update_info,
        ).pack(side="left", anchor="w")
        ttk.Label(
            cfb_combined_row,
            text='— all FBS & FCS conferences in one folder; pair with "Show conference/division"',
            foreground="#555",
        ).pack(side="left", anchor="w", padx=(6, 0))

        # FBS sub-frame
        fbs_frame = ttk.LabelFrame(ncaa_cfb_frame, text="FBS — Football Bowl Subdivision", padding=6)
        fbs_frame.pack(fill="x", pady=(0, 6))

        # FBS combined option
        _fbs_all_row = ttk.Frame(fbs_frame)
        _fbs_all_row.pack(fill="x", pady=(0, 6))
        _fbs_all_set = FLASHCARD_SETS["fbs_all"]
        _fbs_all_var = tk.BooleanVar(value="fbs_all" in default_selected)
        self.set_vars["fbs_all"] = _fbs_all_var
        _fbs_all_count = len(_fbs_all_set.teams) or APPROX_TEAM_COUNTS.get("fbs_all", 0)
        ttk.Checkbutton(
            _fbs_all_row,
            text=f"{_fbs_all_set.display_name} ({_fbs_all_count})" if _fbs_all_count else _fbs_all_set.display_name,
            variable=_fbs_all_var,
            command=self._update_info,
        ).pack(side="left", anchor="w")
        ttk.Label(_fbs_all_row, text="— all FBS conferences in one folder", foreground="#555").pack(
            side="left", anchor="w", padx=(6, 0)
        )

        # Power Four
        p4_frame = ttk.LabelFrame(fbs_frame, text="Power Four", padding=4)
        p4_frame.pack(fill="x", pady=(0, 4))
        _p4_all_row = ttk.Frame(p4_frame)
        _p4_all_row.pack(fill="x", pady=(0, 4))
        _p4_all_set = FLASHCARD_SETS["power_four"]
        _p4_all_var = tk.BooleanVar(value="power_four" in default_selected)
        self.set_vars["power_four"] = _p4_all_var
        _p4_all_count = len(_p4_all_set.teams) or APPROX_TEAM_COUNTS.get("power_four", 0)
        ttk.Checkbutton(
            _p4_all_row,
            text=f"{_p4_all_set.display_name} ({_p4_all_count})" if _p4_all_count else _p4_all_set.display_name,
            variable=_p4_all_var,
            command=self._update_info,
        ).pack(side="left", anchor="w")
        ttk.Label(_p4_all_row, text="— all Power Four conferences in one folder", foreground="#555").pack(
            side="left", anchor="w", padx=(6, 0)
        )
        _p4_grid = ttk.Frame(p4_frame)
        _p4_grid.pack(fill="x")
        for _idx, code in enumerate(["acc", "big_ten", "big_12", "sec"]):
            team_set = FLASHCARD_SETS[code]
            var = tk.BooleanVar(value=code in default_selected)
            self.set_vars[code] = var
            count = len(team_set.teams) or APPROX_TEAM_COUNTS.get(code, 0)
            text = f"{team_set.display_name} ({count})" if count else team_set.display_name
            ttk.Checkbutton(_p4_grid, text=text, variable=var, command=self._update_info).grid(
                row=0, column=_idx, sticky="w", padx=(0, 14), pady=2
            )

        # Group of Five + FBS Independents
        g5_frame = ttk.LabelFrame(fbs_frame, text="Group of Five / Independents", padding=4)
        g5_frame.pack(fill="x")
        _g5_all_row = ttk.Frame(g5_frame)
        _g5_all_row.pack(fill="x", pady=(0, 4))
        _g5_all_set = FLASHCARD_SETS["group_of_five"]
        _g5_all_var = tk.BooleanVar(value="group_of_five" in default_selected)
        self.set_vars["group_of_five"] = _g5_all_var
        _g5_all_count = len(_g5_all_set.teams) or APPROX_TEAM_COUNTS.get("group_of_five", 0)
        ttk.Checkbutton(
            _g5_all_row,
            text=f"{_g5_all_set.display_name} ({_g5_all_count})" if _g5_all_count else _g5_all_set.display_name,
            variable=_g5_all_var,
            command=self._update_info,
        ).pack(side="left", anchor="w")
        ttk.Label(_g5_all_row, text="— all G5 conferences + FBS Independents in one folder", foreground="#555").pack(
            side="left", anchor="w", padx=(6, 0)
        )
        _g5_grid = ttk.Frame(g5_frame)
        _g5_grid.pack(fill="x")
        for _idx, code in enumerate(["aac", "cusa", "mac", "mountain_west", "sun_belt", "pac_12", "fbs_independents"]):
            team_set = FLASHCARD_SETS[code]
            var = tk.BooleanVar(value=code in default_selected)
            self.set_vars[code] = var
            count = len(team_set.teams) or APPROX_TEAM_COUNTS.get(code, 0)
            text = f"{team_set.display_name} ({count})" if count else team_set.display_name
            ttk.Checkbutton(_g5_grid, text=text, variable=var, command=self._update_info).grid(
                row=_idx // 3, column=_idx % 3, sticky="w", padx=(0, 14), pady=2
            )

        # FCS sub-frame
        fcs_frame = ttk.LabelFrame(ncaa_cfb_frame, text="FCS — Football Championship Subdivision", padding=6)
        fcs_frame.pack(fill="x")

        # FCS combined option
        _fcs_all_row = ttk.Frame(fcs_frame)
        _fcs_all_row.pack(fill="x", pady=(0, 6))
        _fcs_all_set = FLASHCARD_SETS["fcs_all"]
        _fcs_all_var = tk.BooleanVar(value="fcs_all" in default_selected)
        self.set_vars["fcs_all"] = _fcs_all_var
        _fcs_all_count = len(_fcs_all_set.teams) or APPROX_TEAM_COUNTS.get("fcs_all", 0)
        ttk.Checkbutton(
            _fcs_all_row,
            text=f"{_fcs_all_set.display_name} ({_fcs_all_count})" if _fcs_all_count else _fcs_all_set.display_name,
            variable=_fcs_all_var,
            command=self._update_info,
        ).pack(side="left", anchor="w")
        ttk.Label(_fcs_all_row, text="— all FCS conferences in one folder", foreground="#555").pack(
            side="left", anchor="w", padx=(6, 0)
        )

        _fcs_grid = ttk.Frame(fcs_frame)
        _fcs_grid.pack(fill="x")
        _fcs_sets = [
            "big_sky", "caa", "ivy_league", "meac",
            "mvfc", "nec", "ovc_big_south", "patriot",
            "pioneer", "socon", "southland", "swac",
            "uac", "fcs_independents",
        ]
        for _idx, code in enumerate(_fcs_sets):
            team_set = FLASHCARD_SETS[code]
            var = tk.BooleanVar(value=code in default_selected)
            self.set_vars[code] = var
            count = len(team_set.teams) or APPROX_TEAM_COUNTS.get(code, 0)
            text = f"{team_set.display_name} ({count})" if count else team_set.display_name
            ttk.Checkbutton(_fcs_grid, text=text, variable=var, command=self._update_info).grid(
                row=_idx // 4, column=_idx % 4, sticky="w", padx=(0, 14), pady=2
            )

        # English Football (Premier League + EFL Family)
        english_frame = ttk.LabelFrame(sets_tab, text="English Football", padding=8)
        english_frame.pack(fill="x", pady=(8, 0))

        english_sets = ["epl", "efl_championship", "efl_league_one", "efl_league_two"]

        for index, code in enumerate(english_sets):
            row = index // 2
            col = index % 2
            team_set = FLASHCARD_SETS[code]
            var = tk.BooleanVar(value=code in default_selected)
            self.set_vars[code] = var

            count = len(team_set.teams) or APPROX_TEAM_COUNTS.get(code, 0)
            text = f"{team_set.display_name} ({count})" if count else team_set.display_name
            chk = ttk.Checkbutton(english_frame, text=text, variable=var, command=self._update_info)
            chk.grid(row=row, column=col, sticky="w", padx=(0, 14), pady=2)

        # International Football (Soccer)
        intl_soccer_frame = ttk.LabelFrame(sets_tab, text="International Football (Soccer)", padding=8)
        intl_soccer_frame.pack(fill="x", pady=(8, 0))

        intl_soccer_sets = ["la_liga", "bundesliga", "serie_a", "ligue_1"]

        for index, code in enumerate(intl_soccer_sets):
            row = index // 2
            col = index % 2
            team_set = FLASHCARD_SETS[code]
            var = tk.BooleanVar(value=code in default_selected)
            self.set_vars[code] = var

            count = len(team_set.teams) or APPROX_TEAM_COUNTS.get(code, 0)
            text = f"{team_set.display_name} ({count})" if count else team_set.display_name
            chk = ttk.Checkbutton(intl_soccer_frame, text=text, variable=var, command=self._update_info)
            chk.grid(row=row, column=col, sticky="w", padx=(0, 14), pady=2)

        # Spacer to push content to top and allow tab expansion
        spacer = ttk.Frame(sets_tab)
        spacer.pack(fill="both", expand=True)

        # ============ TAB 2: SETTINGS ============
        settings_tab = ttk.Frame(main_tabs, padding=10)
        main_tabs.add(settings_tab, text="Settings")

        # General Settings
        general_frame = ttk.LabelFrame(settings_tab, text="General Settings", padding=10)
        general_frame.pack(fill="x", pady=(0, 8))
        general_frame.columnconfigure(1, weight=1)
        general_frame.columnconfigure(3, weight=1)

        ttk.Label(general_frame, text="Image DPI").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        self.dpi_var = tk.IntVar(value=300)
        dpi_scale = ttk.Scale(
            general_frame,
            from_=150,
            to=600,
            variable=self.dpi_var,
            orient="horizontal",
            command=self._update_dpi_label,
        )
        dpi_scale.grid(row=0, column=1, sticky="ew", pady=4)
        self.dpi_label = ttk.Label(general_frame, text="300", width=5)
        self.dpi_label.grid(row=0, column=2, sticky="e", padx=(8, 0), pady=4)
        ttk.Label(
            general_frame,
            text="Print quality. 300 is standard; higher is sharper but creates larger files.",
            foreground="#555",
        ).grid(row=0, column=3, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(general_frame, text="Card Size (W x H)").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)
        self.card_ratio_var = tk.StringVar(value="3x2")
        ratio_combo = ttk.Combobox(
            general_frame,
            textvariable=self.card_ratio_var,
            values=["1x1", "3x2", "2x3", "5x4", "4x5", "7x5", "5x7", "8x10", "10x8"],
            state="readonly",
            width=12,
        )
        ratio_combo.grid(row=1, column=1, sticky="w", pady=4)
        self.ratio_help_label = ttk.Label(
            general_frame,
            text="",
            foreground="#555",
        )
        self.ratio_help_label.grid(row=1, column=3, sticky="w", padx=(10, 0), pady=4)
        self._update_ratio_help_label()

        ttk.Label(general_frame, text="Output Folder").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=4)
        self.output_var = tk.StringVar(value="output")
        output_entry = ttk.Entry(general_frame, textvariable=self.output_var)
        output_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)
        ttk.Label(
            general_frame,
            text="Base folder. One subfolder per selected set is created automatically.",
            foreground="#555",
        ).grid(row=2, column=3, sticky="w", padx=(10, 0), pady=4)

        self.force_refresh_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            general_frame,
            text="Force re-download logos (ignore cache)",
            variable=self.force_refresh_var,
        ).grid(row=3, column=1, columnspan=3, sticky="w", pady=(2, 4))

        # ── Row: Card Types | Filename Pattern ───────────────────────────────
        card_row = ttk.Frame(settings_tab)
        card_row.pack(fill="x", pady=(0, 8))
        card_row.columnconfigure(0, weight=1)
        card_row.columnconfigure(1, weight=1)

        card_types_frame = ttk.LabelFrame(card_row, text="Card Types", padding=10)
        card_types_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.card_type_logo_var = tk.BooleanVar(value=True)
        self.card_type_text_var = tk.BooleanVar(value=True)
        self.card_type_combo_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card_types_frame, text="Logo  — logo only", variable=self.card_type_logo_var, command=self._on_card_types_changed).pack(anchor="w", pady=2)
        ttk.Checkbutton(card_types_frame, text="Text  — team name only", variable=self.card_type_text_var, command=self._on_card_types_changed).pack(anchor="w", pady=2)
        ttk.Checkbutton(card_types_frame, text="Combined  — logo + name", variable=self.card_type_combo_var, command=self._on_card_types_changed).pack(anchor="w", pady=2)

        filename_frame = ttk.LabelFrame(card_row, text="Filename Pattern", padding=8)
        filename_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        self.filename_format_var = tk.StringVar(value="prefix")
        ttk.Radiobutton(
            filename_frame,
            text="Prefix: CARDTYPE_TEAMTEXT.png",
            variable=self.filename_format_var,
            value="prefix",
        ).pack(anchor="w", pady=1)
        ttk.Radiobutton(
            filename_frame,
            text="Suffix: TEAMTEXT_CARDTYPE.png",
            variable=self.filename_format_var,
            value="suffix",
        ).pack(anchor="w", pady=1)
        ttk.Label(
            filename_frame,
            text="CARDTYPE is logo, text, or combo.",
            foreground="#555",
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        # ── Row: Name Format | Name Order ─────────────────────────────────────
        name_row = ttk.Frame(settings_tab)
        name_row.pack(fill="x", pady=(0, 8))
        name_row.columnconfigure(0, weight=1)
        name_row.columnconfigure(1, weight=1)

        name_frame = ttk.LabelFrame(name_row, text="Name Format", padding=8)
        name_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.name_format_var = tk.StringVar(value="full")
        self.name_full_btn = ttk.Radiobutton(
            name_frame,
            text="Full name (location + team)",
            variable=self.name_format_var,
            value="full",
            command=self._on_name_format_changed,
        )
        self.name_full_btn.pack(anchor="w", pady=1)
        self.name_team_btn = ttk.Radiobutton(
            name_frame,
            text="Team name only",
            variable=self.name_format_var,
            value="team_only",
            command=self._on_name_format_changed,
        )
        self.name_team_btn.pack(anchor="w", pady=1)
        self.name_city_btn = ttk.Radiobutton(
            name_frame,
            text="City / location only",
            variable=self.name_format_var,
            value="city_only",
            command=self._on_name_format_changed,
        )
        self.name_city_btn.pack(anchor="w", pady=1)

        name_order_frame = ttk.LabelFrame(name_row, text="Name Order", padding=8)
        name_order_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        ttk.Label(
            name_order_frame,
            text="Applies to full-name mode only.",
            foreground="#555",
        ).pack(anchor="w", pady=(0, 6))
        self.name_order_var = tk.StringVar(value="city_first")
        ttk.Radiobutton(
            name_order_frame,
            text="City first  (e.g. Boston Red Sox)",
            variable=self.name_order_var,
            value="city_first",
        ).pack(anchor="w", pady=1)
        ttk.Radiobutton(
            name_order_frame,
            text="Team first  (e.g. Red Sox Boston)",
            variable=self.name_order_var,
            value="team_first",
        ).pack(anchor="w", pady=1)

        # ── Row: Text Colors | Typography & Effects ───────────────────────────
        appearance_row = ttk.Frame(settings_tab)
        appearance_row.pack(fill="x", pady=(0, 0))
        appearance_row.columnconfigure(0, weight=1)
        appearance_row.columnconfigure(1, weight=1)

        # Left: Text Colors
        colors_frame = ttk.LabelFrame(appearance_row, text="Text Colors", padding=10)
        colors_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.split_text_colors_var = tk.BooleanVar(value=False)
        self.split_text_colors_btn = ttk.Checkbutton(
            colors_frame,
            text="Use separate colors for location and team name",
            variable=self.split_text_colors_var,
            command=self._on_split_color_toggle,
        )
        self.split_text_colors_btn.pack(anchor="w", pady=(0, 2))

        self.split_color_policy_label = ttk.Label(
            colors_frame,
            text="",
            foreground="#666",
            wraplength=280,
            justify="left",
        )
        self.split_color_policy_label.pack(anchor="w", pady=(0, 4))

        self.color_inputs_frame = ttk.Frame(colors_frame)
        self.color_inputs_frame.pack(anchor="w")

        ttk.Label(self.color_inputs_frame, text="Text color").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=2
        )
        self.text_color_var = tk.StringVar(value="black")
        self.text_color_entry = ttk.Entry(
            self.color_inputs_frame,
            textvariable=self.text_color_var,
            width=12,
        )
        self.text_color_entry.grid(row=0, column=1, sticky="w", pady=2, padx=(0, 6))
        self.text_color_swatch = tk.Label(
            self.color_inputs_frame, text="", width=3, relief="solid", bd=1
        )
        self.text_color_swatch.grid(row=0, column=2, sticky="w", pady=2)
        ttk.Label(self.color_inputs_frame, text="Split off", foreground="#777").grid(
            row=0, column=3, sticky="w", padx=(8, 0), pady=2
        )

        ttk.Label(self.color_inputs_frame, text="Location color").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=2
        )
        self.location_color_var = tk.StringVar(value="#1f4e79")
        self.location_color_entry = ttk.Entry(
            self.color_inputs_frame,
            textvariable=self.location_color_var,
            width=12,
        )
        self.location_color_entry.grid(row=1, column=1, sticky="w", pady=2, padx=(0, 6))
        self.location_color_swatch = tk.Label(
            self.color_inputs_frame, text="", width=3, relief="solid", bd=1
        )
        self.location_color_swatch.grid(row=1, column=2, sticky="w", pady=2)
        ttk.Label(self.color_inputs_frame, text="Split on", foreground="#777").grid(
            row=1, column=3, sticky="w", padx=(8, 0), pady=2
        )

        ttk.Label(self.color_inputs_frame, text="Team color").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=2
        )
        self.team_color_var = tk.StringVar(value="#b22222")
        self.team_color_entry = ttk.Entry(
            self.color_inputs_frame,
            textvariable=self.team_color_var,
            width=12,
        )
        self.team_color_entry.grid(row=2, column=1, sticky="w", pady=2, padx=(0, 6))
        self.team_color_swatch = tk.Label(
            self.color_inputs_frame, text="", width=3, relief="solid", bd=1
        )
        self.team_color_swatch.grid(row=2, column=2, sticky="w", pady=2)
        ttk.Label(self.color_inputs_frame, text="Split on", foreground="#777").grid(
            row=2, column=3, sticky="w", padx=(8, 0), pady=2
        )

        self.color_hint_label = ttk.Label(
            colors_frame,
            text="Use hex (#RRGGBB) or named colors (black, navy, red, …).",
            foreground="#555",
            wraplength=280,
        )
        self.color_hint_label.pack(anchor="w", pady=(6, 0))

        ttk.Label(
            colors_frame,
            text="Note: soccer sets use only Text color regardless of split setting.",
            foreground="#888",
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # Right: Typography & Effects
        typography_frame = ttk.LabelFrame(appearance_row, text="Typography & Effects", padding=10)
        typography_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        size_row = ttk.Frame(typography_frame)
        size_row.pack(anchor="w")
        ttk.Label(size_row, text="Text font size:").pack(side="left", padx=(0, 10))
        self.text_size_var = tk.StringVar(value="large")
        for label, value in (("Large", "large"), ("Medium", "medium"), ("Small", "small")):
            ttk.Radiobutton(
                size_row,
                text=label,
                variable=self.text_size_var,
                value=value,
            ).pack(side="left", padx=(0, 8))
        ttk.Label(
            typography_frame,
            text="Large fills the card; smaller sizes leave more white space.",
            foreground="#555",
            wraplength=280,
        ).pack(anchor="w", pady=(2, 8))

        # Background color
        bg_row = ttk.Frame(typography_frame)
        bg_row.pack(anchor="w", fill="x", pady=(0, 4))
        ttk.Label(bg_row, text="Background:").pack(side="left", padx=(0, 8))
        self.bg_color_var = tk.StringVar(value="white")
        ttk.Entry(bg_row, textvariable=self.bg_color_var, width=12).pack(side="left", padx=(0, 6))
        self.bg_color_swatch = tk.Label(bg_row, text="", width=3, relief="solid", bd=1)
        self.bg_color_swatch.pack(side="left", padx=(0, 8))
        ttk.Label(bg_row, text="All card types.", foreground="#777").pack(side="left")

        # Text effect
        effect_row = ttk.Frame(typography_frame)
        effect_row.pack(anchor="w", fill="x", pady=(0, 2))
        ttk.Label(effect_row, text="Text effect:").pack(side="left", padx=(0, 8))
        self.text_effect_var = tk.StringVar(value="none")
        for lbl, val in (("None", "none"), ("Shadow", "shadow"), ("Outline", "outline")):
            ttk.Radiobutton(effect_row, text=lbl, variable=self.text_effect_var, value=val).pack(
                side="left", padx=(0, 6)
            )
        effect_color_row = ttk.Frame(typography_frame)
        effect_color_row.pack(anchor="w", fill="x", pady=(0, 4))
        ttk.Label(effect_color_row, text="Effect color:").pack(side="left", padx=(0, 8))
        self.text_effect_color_var = tk.StringVar(value="#888888")
        ttk.Entry(effect_color_row, textvariable=self.text_effect_color_var, width=10).pack(side="left", padx=(0, 6))
        self.text_effect_color_swatch = tk.Label(effect_color_row, text="", width=3, relief="solid", bd=1)
        self.text_effect_color_swatch.pack(side="left")

        # Logo filter
        filter_row = ttk.Frame(typography_frame)
        filter_row.pack(anchor="w", fill="x", pady=(0, 0))
        ttk.Label(filter_row, text="Logo filter:").pack(side="left", padx=(0, 8))
        self.logo_filter_var = tk.StringVar(value="none")
        for lbl, val in (("None", "none"), ("Grayscale", "grayscale"), ("Sepia", "sepia")):
            ttk.Radiobutton(filter_row, text=lbl, variable=self.logo_filter_var, value=val).pack(
                side="left", padx=(0, 6)
            )

        # ── Row: Conference / Division (left) + Card Index (right) ──────────
        conf_index_row = ttk.Frame(settings_tab)
        conf_index_row.pack(fill="x", pady=(8, 0))
        conf_index_row.columnconfigure(0, weight=1)
        conf_index_row.columnconfigure(1, weight=1)

        conf_frame = ttk.LabelFrame(conf_index_row, text="Conference / Division", padding=10)
        conf_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.show_conference_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            conf_frame,
            text="Show conference / division below team name",
            variable=self.show_conference_var,
        ).pack(anchor="w")

        self.abbreviate_conference_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            conf_frame,
            text='Abbreviate  (e.g. "AL · East")',
            variable=self.abbreviate_conference_var,
        ).pack(anchor="w", pady=(4, 0))

        ttk.Label(
            conf_frame,
            text="Applies to text and combo cards for MLB, NFL, NBA, NHL, WNBA, MLS, and CFB All Conferences.",
            foreground="#555",
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        self.show_abbreviation_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            conf_frame,
            text="Show team abbreviation  (e.g. OSU, UNC, WVU)",
            variable=self.show_abbreviation_var,
        ).pack(anchor="w", pady=(8, 0))
        ttk.Label(
            conf_frame,
            text="Applies to FBS college football sets only. Other sets are unaffected.",
            foreground="#555",
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        index_frame = ttk.LabelFrame(conf_index_row, text='Card Index  (e.g. "1/18")', padding=10)
        index_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        self.index_corner_var = tk.StringVar(value="none")
        index_grid = ttk.Frame(index_frame)
        index_grid.pack(anchor="w")

        ttk.Radiobutton(index_grid, text="Off", variable=self.index_corner_var, value="none").grid(
            row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 6)
        )
        for col, (lbl, val) in enumerate([("Top-left", "top-left"), ("Top-center", "top-center"), ("Top-right", "top-right")]):
            ttk.Radiobutton(index_grid, text=lbl, variable=self.index_corner_var, value=val).grid(
                row=1, column=col, sticky="w", padx=(0, 6), pady=2
            )
        for col, (lbl, val) in enumerate([("Bottom-left", "bottom-left"), ("Bottom-center", "bottom-center"), ("Bottom-right", "bottom-right")]):
            ttk.Radiobutton(index_grid, text=lbl, variable=self.index_corner_var, value=val).grid(
                row=2, column=col, sticky="w", padx=(0, 6), pady=2
            )

        ttk.Label(
            index_frame,
            text="Tip: choose a different position than the league logo overlay.",
            foreground="#555",
            wraplength=280,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        # ── League Logo Overlay (full width) ─────────────────────────────────
        overlay_frame = ttk.LabelFrame(settings_tab, text="League Logo Overlay", padding=10)
        overlay_frame.pack(fill="x", pady=(8, 0))

        self.league_logo_corner_var = tk.StringVar(value="none")
        logo_corner_row = ttk.Frame(overlay_frame)
        logo_corner_row.pack(anchor="w")
        for label, value in [
            ("None (off)", "none"),
            ("Top-left", "top-left"),
            ("Top-center", "top-center"),
            ("Top-right", "top-right"),
            ("Bottom-left", "bottom-left"),
            ("Bottom-center", "bottom-center"),
            ("Bottom-right", "bottom-right"),
        ]:
            ttk.Radiobutton(
                logo_corner_row,
                text=label,
                variable=self.league_logo_corner_var,
                value=value,
            ).pack(side="left", padx=(0, 12))
        ttk.Label(
            overlay_frame,
            text="Places a small league / conference logo in the selected corner of every card. "
                 "The logo is downloaded automatically alongside team logos.",
            foreground="#555",
            wraplength=560,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        # ── PDF Output ────────────────────────────────────────────────────────
        pdf_frame = ttk.LabelFrame(settings_tab, text="PDF Output", padding=10)
        pdf_frame.pack(fill="x", pady=(8, 0))

        self.pdf_output_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pdf_frame,
            text="Also generate a PDF (one card per page, duplex-ready front/back order)",
            variable=self.pdf_output_var,
        ).pack(anchor="w")
        ttk.Label(
            pdf_frame,
            text=(
                "Saves {set_code}_flashcards.pdf alongside the PNGs. "
                "With Logo + Text selected, pages alternate logo/text per team — "
                "print duplex (flip on short edge) to get aligned fronts and backs."
            ),
            foreground="#555",
            wraplength=560,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        # Initialize dependent state
        self._on_name_format_changed()
        self._on_split_color_toggle()

        # ============ TAB 3: OUTPUT ============
        output_tab = ttk.Frame(main_tabs, padding=10)
        main_tabs.add(output_tab, text="Output")

        output_tab.columnconfigure(0, weight=1)
        output_tab.rowconfigure(1, weight=1)

        # Filename preview
        preview_frame = ttk.LabelFrame(output_tab, text="Filename Preview", padding=10)
        preview_frame.pack(fill="x", pady=(0, 8))
        preview_frame.columnconfigure(0, weight=1)

        self.preview_limit_label = ttk.Label(
            preview_frame,
            text="",
            foreground="#555",
        )
        self.preview_limit_label.pack(anchor="w", pady=(0, 4))

        self.preview_text = tk.Text(
            preview_frame,
            height=6,
            state="disabled",
            font=("Courier", 9),
        )
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scrollbar = ttk.Scrollbar(preview_frame, command=self.preview_text.yview)
        preview_scrollbar.pack(side="right", fill="y")
        self.preview_text.config(yscrollcommand=preview_scrollbar.set)

        # Results tabs (Summary and Run Log)
        self.output_tabs = ttk.Notebook(output_tab)
        self.output_tabs.pack(fill="both", expand=True, pady=(0, 0))

        config_tab = ttk.Frame(self.output_tabs, padding=8)
        status_tab = ttk.Frame(self.output_tabs, padding=8)
        self.output_tabs.add(config_tab, text="Summary")
        self.output_tabs.add(status_tab, text="Run Log")

        self.info_text = tk.Text(config_tab, height=6, state="disabled", font=("Courier", 9))
        self.info_text.pack(side="left", fill="both", expand=True)
        info_scrollbar = ttk.Scrollbar(config_tab, command=self.info_text.yview)
        info_scrollbar.pack(side="right", fill="y")
        self.info_text.config(yscrollcommand=info_scrollbar.set)

        self.status_text = tk.Text(status_tab, height=6, state="disabled", font=("Courier", 9))
        self.status_text.pack(side="left", fill="both", expand=True)
        status_scrollbar = ttk.Scrollbar(status_tab, command=self.status_text.yview)
        status_scrollbar.pack(side="right", fill="y")
        self.status_text.config(yscrollcommand=status_scrollbar.set)

        # --- Buttons (fixed at bottom) ---
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill="x", padx=10, pady=(8, 10))

        self.generate_btn = ttk.Button(
            button_frame, text="Generate Flashcards (Ctrl+G)", command=self._on_generate_click
        )
        self.generate_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.open_btn = ttk.Button(
            button_frame,
            text="Open Output Folder (Ctrl+O)",
            command=self._on_open_folder_click,
            state="disabled",
        )
        self.open_btn.pack(side="left", fill="x", expand=True, padx=5)

        ttk.Button(button_frame, text="Close", command=self.root.quit).pack(
            side="left", fill="x", expand=True, padx=(5, 0)
        )

        # Keep info panel up to date when options change.
        for var in (
            self.output_var,
            self.filename_format_var,
            self.name_format_var,
            self.name_order_var,
            self.split_text_colors_var,
            self.text_color_var,
            self.location_color_var,
            self.team_color_var,
            self.text_size_var,
            self.card_type_logo_var,
            self.card_type_text_var,
            self.card_type_combo_var,
            self.league_logo_corner_var,
            self.show_conference_var,
            self.abbreviate_conference_var,
            self.show_abbreviation_var,
            self.index_corner_var,
            self.bg_color_var,
            self.text_effect_var,
            self.text_effect_color_var,
            self.logo_filter_var,
            self.pdf_output_var,
        ):
            var.trace_add("write", lambda *_: self._update_info())
        self.card_ratio_var.trace_add("write", lambda *_: self._on_card_ratio_changed())

        # Initial info display
        self._update_info()

    def _update_dpi_label(self, value: str) -> None:
        """Update DPI display label."""
        self.dpi_label.config(text=str(int(float(value))))
        self._update_info()

    def _on_card_ratio_changed(self) -> None:
        """Refresh ratio explainer and info text when ratio changes."""
        self._update_ratio_help_label()
        self._update_info()

    def _on_card_types_changed(self) -> None:
        """Refresh split-color state and info text when card types change."""
        self._on_split_color_toggle()
        self._update_info()

    def _selected_card_types(self) -> set[str]:
        """Return the set of selected card type codes."""
        types: set[str] = set()
        if self.card_type_logo_var.get():
            types.add("logo")
        if self.card_type_text_var.get():
            types.add("text")
        if self.card_type_combo_var.get():
            types.add("combo")
        return types

    def _update_ratio_help_label(self) -> None:
        """Show width x height meaning and orientation for selected ratio."""
        ratio = self.card_ratio_var.get()
        dimensions, orientation = self.RATIO_META.get(ratio, ("unknown", "unknown"))
        self.ratio_help_label.config(
            text=f"Width x height: {dimensions} ({orientation})."
        )

    def _on_name_format_changed(self) -> None:
        """Update UI state based on name format."""
        self._on_split_color_toggle()

    def _refresh_color_swatches(self) -> None:
        """Update swatch labels to reflect current color entry values."""
        for swatch, var in (
            (self.text_color_swatch, self.text_color_var),
            (self.location_color_swatch, self.location_color_var),
            (self.team_color_swatch, self.team_color_var),
            (self.bg_color_swatch, self.bg_color_var),
            (self.text_effect_color_swatch, self.text_effect_color_var),
        ):
            try:
                swatch.config(bg=var.get())
            except tk.TclError:
                swatch.config(bg="#cccccc")

    def _on_split_color_toggle(self) -> None:
        """Enable/disable split-color controls based on mode and name format."""
        selected_codes = self._selected_set_codes()
        forced_off_codes = [
            code
            for code in selected_codes
            if code in self.SPLIT_COLOR_DISABLED_SET_CODES
        ]
        forced_off = bool(forced_off_codes)

        if forced_off and self.split_text_colors_var.get():
            self.split_text_colors_var.set(False)

        card_types = self._selected_card_types()
        text_is_rendered = "text" in card_types or "combo" in card_types
        split_toggle_state = "normal" if (text_is_rendered and not forced_off) else "disabled"
        self.split_text_colors_btn.config(state=split_toggle_state)

        if forced_off:
            league_names = [FLASHCARD_SETS[code].display_name for code in forced_off_codes]
            self.split_color_policy_label.config(
                text=(
                    "Split colors are disabled for selected soccer sets: "
                    + ", ".join(league_names)
                    + "."
                )
            )
        else:
            if "mls" in selected_codes and text_is_rendered:
                self.split_color_policy_label.config(
                    text="MLS supports split colors. Enable the checkbox if you want location/team color separation."
                )
            else:
                self.split_color_policy_label.config(text="")

        self.location_color_entry.config(state="normal")
        self.team_color_entry.config(state="normal")
        self.text_color_entry.config(state="normal")

    def _selected_set_codes(self) -> list[str]:
        """Return selected set codes in sorted order."""
        return [code for code in sorted(self.set_vars.keys()) if self.set_vars[code].get()]

    def _select_all_sets(self) -> None:
        """Select all available sets."""
        for var in self.set_vars.values():
            var.set(True)
        self._update_info()

    def _clear_set_selection(self) -> None:
        """Clear all selected sets."""
        for var in self.set_vars.values():
            var.set(False)
        self._update_info()

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Scroll the main form with mouse wheel."""
        if not self._main_canvas:
            return
        delta = int(-1 * (event.delta / 120))
        self._main_canvas.yview_scroll(delta, "units")

    def _reset_window_size(self) -> None:
        """Reset window to default geometry."""
        self.root.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")

    def _fit_to_content(self) -> None:
        """Resize window to fit content while respecting screen and minimum bounds."""
        if not self._main_canvas:
            return

        self.root.update_idletasks()

        # Scrollregion is "x1 y1 x2 y2" from the canvas.
        region = self._main_canvas.cget("scrollregion")
        if not region:
            return

        try:
            _x1, _y1, x2, y2 = [int(float(v)) for v in str(region).split()]
        except ValueError:
            return

        # Add room for borders, menu bar, and right-side scrollbar.
        desired_width = x2 + 40
        desired_height = y2 + 80

        # Keep size usable on smaller displays.
        max_width = int(self.root.winfo_screenwidth() * 0.95)
        max_height = int(self.root.winfo_screenheight() * 0.90)

        width = max(self.MIN_WIDTH, min(desired_width, max_width))
        height = max(self.MIN_HEIGHT, min(desired_height, max_height))

        self.root.geometry(f"{width}x{height}")

    def _update_info(self) -> None:
        """Update the info display box."""
        selected_codes = self._selected_set_codes()
        self._on_split_color_toggle()
        selected_display = [FLASHCARD_SETS[code].display_name for code in selected_codes]
        split_forced_off = any(
            code in self.SPLIT_COLOR_DISABLED_SET_CODES for code in selected_codes
        )

        # Distinguish between configured (static) and API-driven (dynamic) teams
        configured_teams = 0
        api_driven_count = 0
        for code in selected_codes:
            team_count = len(FLASHCARD_SETS[code].teams)
            if team_count > 0:
                configured_teams += team_count
            else:
                api_driven_count += 1

        team_count_str = f"{configured_teams} configured"
        if api_driven_count > 0:
            team_count_str += f" + {api_driven_count} API-driven (actual count after download)"
        card_types = self._selected_card_types()
        output_multiplier = len(card_types)
        files_est = f"{configured_teams * output_multiplier}" if configured_teams > 0 else "(varies)"

        info_lines = [
            f"Sets: {', '.join(selected_display) if selected_display else '(none selected)'}",
            f"Set count: {len(selected_codes)}",
            f"Teams: {team_count_str}",
            f"Files (estimated): {files_est}",
            f"DPI: {self.dpi_var.get()}",
            f"Ratio: {self.card_ratio_var.get()} ({self.RATIO_META.get(self.card_ratio_var.get(), ('unknown', 'unknown'))[0]}, {self.RATIO_META.get(self.card_ratio_var.get(), ('unknown', 'unknown'))[1]})",
            f"Card types: {', '.join(sorted(card_types)) if card_types else '(none)'}",
            f"Filename: {self.filename_format_var.get()}",
            f"Name: {self.name_format_var.get()} ({self.name_order_var.get()})",
            (
                "Split colors: off (disabled for selected soccer sets)"
                if split_forced_off
                else f"Split colors: {'on' if self.split_text_colors_var.get() else 'off'}"
            ),
            f"Colors: text={self.text_color_var.get()} location={self.location_color_var.get()} team={self.team_color_var.get()}",
            f"Text size: {self.text_size_var.get()}",
            f"Background: {self.bg_color_var.get()}",
            f"Text effect: {self.text_effect_var.get()}"
            + (f" (color: {self.text_effect_color_var.get()})" if self.text_effect_var.get() != "none" else ""),
            f"Logo filter: {self.logo_filter_var.get()}",
            f"Conference/division: {'on' if self.show_conference_var.get() else 'off'}"
            + (" (abbreviated)" if self.abbreviate_conference_var.get() else ""),
            f"Team abbreviation: {'on' if self.show_abbreviation_var.get() else 'off'}",
            f"Card index: {self.index_corner_var.get()}",
            f"League logo overlay: {self.league_logo_corner_var.get()}",
            f"PDF output: {'on' if self.pdf_output_var.get() else 'off'}",
            f"Output folder: {self.output_var.get()} (set subfolders appended)",
            f"Logos: data/logos_raw/",
        ]

        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, "\n".join(info_lines))
        self.info_text.config(state="disabled")
        self._refresh_color_swatches()
        self._update_filename_preview(selected_codes)

        output_folder = Path(self.output_var.get())
        if output_folder.exists() and output_folder.is_dir():
            self.open_btn.config(state="normal")
            self.output_path = str(output_folder.resolve())

    def _preview_teams(self, selected_codes: list[str]) -> list[tuple[str, Team]]:
        """Build one representative team preview for each selected set."""
        if not selected_codes:
            return [(
                "sample",
                Team(
                    name="Sample City Mascots",
                    location_name="Sample City",
                    mascot_name="Mascots",
                ),
            )]

        previews: list[tuple[str, Team]] = []
        for code in selected_codes:
            teams = FLASHCARD_SETS[code].teams
            if teams:
                sample_team = sorted(teams, key=lambda team: team.name.lower())[0]
            else:
                sample_team = Team(
                    name="Sample City Mascots",
                    location_name="Sample City",
                    mascot_name="Mascots",
                )
            previews.append((code, sample_team))

        return previews

    def _update_filename_preview(self, selected_codes: list[str]) -> None:
        """Refresh filename previews for selected sets with a bounded list."""
        previews = self._preview_teams(selected_codes)
        shown_previews = previews[: self.MAX_FILENAME_PREVIEW_SETS]
        hidden_count = max(0, len(previews) - len(shown_previews))

        lines: list[str] = []
        for code, team in shown_previews:
            output_names = format_output_filenames(
                team,
                filename_format=self.filename_format_var.get(),
                name_format=self.name_format_var.get(),
                name_order=self.name_order_var.get(),
                card_types=self._selected_card_types(),
            )
            display_name = FLASHCARD_SETS[code].display_name if code in FLASHCARD_SETS else "Sample"
            lines.append(f"[{display_name}] source: {team.name}")
            for output_name in output_names:
                lines.append(f"  file : {output_name}.png")

        if hidden_count:
            lines.append(f"... and {hidden_count} more set previews")

        self.preview_limit_label.config(
            text=(
                f"Showing up to {self.MAX_FILENAME_PREVIEW_SETS} selected set previews."
                if selected_codes
                else "No sets selected; showing sample naming preview."
            )
        )
        self.preview_text.config(state="normal")
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, "\n".join(lines))
        self.preview_text.config(state="disabled")

    def _on_generate_click(self) -> None:
        """Handle Generate button click."""
        if self.is_generating:
            messagebox.showwarning(
                "Generation In Progress", "A generation run is already in progress. Please wait."
            )
            return

        # Update info
        self._update_info()

        # Run generation in background thread to not freeze UI
        thread = threading.Thread(target=self._generate_flashcards, daemon=True)
        thread.start()

    def _generate_flashcards(self) -> None:
        """Generate flashcards (runs in background thread)."""
        self.is_generating = True
        self.generate_btn.config(state="disabled")
        self.generation_start_time = time.time()
        
        # Switch to Run Log tab immediately to show progress
        self.output_tabs.select(1)

        try:
            set_codes = self._selected_set_codes()
            if not set_codes:
                self._set_status("✗ Error:\nSelect at least one set.")
                messagebox.showwarning("No Sets Selected", "Select at least one set to generate.")
                return

            output_dir = self.output_var.get()
            dpi = self.dpi_var.get()
            card_ratio = self.card_ratio_var.get()
            card_types = self._selected_card_types()
            if not card_types:
                self._set_status("\u2717 Error:\nSelect at least one card type (Logo, Text, or Combined).")
                messagebox.showwarning("No Card Types Selected", "Select at least one card type (Logo, Text, or Combined).")
                return
            filename_format = self.filename_format_var.get()
            name_format = self.name_format_var.get()
            split_text_colors = self.split_text_colors_var.get()
            text_color = self.text_color_var.get()
            location_color = self.location_color_var.get()
            team_color = self.team_color_var.get()
            bg_color = self.bg_color_var.get()
            text_effect = self.text_effect_var.get()
            text_effect_color = self.text_effect_color_var.get()
            logo_filter = self.logo_filter_var.get()
            league_logo_corner = self.league_logo_corner_var.get()
            text_size = self.text_size_var.get()
            show_conference = self.show_conference_var.get()
            abbreviate_conference = self.abbreviate_conference_var.get()
            show_abbreviation = self.show_abbreviation_var.get()
            index_corner = self.index_corner_var.get()
            force_refresh = self.force_refresh_var.get()
            pdf_output = self.pdf_output_var.get()
            valid_colors, invalid_msg = self._validate_colors(text_color, location_color, team_color, bg_color, text_effect_color)
            if not valid_colors:
                self._set_status(f"✗ Error:\n{invalid_msg}")
                messagebox.showerror("Invalid Color", invalid_msg)
                return

            # Verify the output folder is writable before starting.
            if output_dir:
                output_dir_path = Path(output_dir)
                try:
                    output_dir_path.mkdir(parents=True, exist_ok=True)
                    _test_file = output_dir_path / ".write_test"
                    _test_file.write_text("", encoding="utf-8")
                    _test_file.unlink()
                except PermissionError:
                    msg = f"Cannot write to output folder:\n{output_dir_path}\n\nCheck folder permissions."
                    self._set_status("✗ Error:\nOutput folder is not writable.")
                    messagebox.showerror("Permission Error", msg)
                    return
                except OSError as _e:
                    msg = f"Cannot access output folder:\n{output_dir_path}\n\n{_e}"
                    self._set_status("✗ Error:\nInvalid output folder.")
                    messagebox.showerror("Invalid Output Folder", msg)
                    return

            # Call pure business logic
            self._append_status("Starting generation...")
            self._append_status(f"Sets selected: {', '.join([FLASHCARD_SETS[code].display_name for code in set_codes])}")
            self._append_status(f"Options: ratio={card_ratio}, dpi={dpi}, types={','.join(sorted(card_types))}, name={name_format}")
            self._append_status("")

            def log_progress(message: str) -> None:
                self._append_status(message)

            result = generate_flashcards_batch(
                set_codes=set_codes,
                output_dir=output_dir,
                dpi=dpi,
                card_ratio=card_ratio,
                card_types=card_types,
                filename_format=filename_format,
                name_format=name_format,
                name_order=self.name_order_var.get(),
                split_text_colors=split_text_colors,
                text_color=text_color,
                text_size=text_size,
                location_color=location_color,
                team_color=team_color,
                bg_color=bg_color,
                text_effect=text_effect,
                text_effect_color=text_effect_color,
                logo_filter=logo_filter,
                show_conference=show_conference,
                abbreviate_conference=abbreviate_conference,
                show_abbreviation=show_abbreviation,
                index_corner=index_corner,
                league_logo_corner=league_logo_corner,
                pdf_output=pdf_output,
                force_refresh=force_refresh,
                progress_callback=log_progress,
            )

            result_status = str(result.get("status", "error"))
            raw_success_count = result.get("success_count", 0)
            success_count = raw_success_count if isinstance(raw_success_count, int) else 0
            raw_set_count = result.get("set_count", 0)
            set_count = raw_set_count if isinstance(raw_set_count, int) else 0
            raw_error_count = result.get("error_count", 0)
            error_count = raw_error_count if isinstance(raw_error_count, int) else 0
            raw_results = result.get("results", [])
            per_set_results = raw_results if isinstance(raw_results, list) else []
            raw_warnings = result.get("warnings", [])
            warning_items = [str(warning) for warning in raw_warnings] if isinstance(raw_warnings, list) else []

            if result_status in ("success", "partial"):
                self.output_path = str(Path(output_dir).resolve())
                self.open_btn.config(state="normal")

                # Log per-set details
                self._append_status(f"{'✓ Success' if result_status == 'success' else '⚠ Partial Success'}: batch generation complete")
                self._append_status(f"Sets processed: {success_count}/{set_count} succeeded")
                if error_count > 0:
                    self._append_status(f"Failed sets: {error_count}")
                
                self._append_status("")
                self._append_status("Per-set results:")
                for item in per_set_results:
                    if not isinstance(item, dict):
                        continue
                    if item.get("status") == "success":
                        self._append_status(
                            f"  ✓ {item.get('display_name', '?')}: {item.get('team_count', 0)} teams → {item.get('file_count', 0)} cards"
                        )
                        if item.get("pdf_path"):
                            self._append_status(f"    PDF: {Path(str(item.get('pdf_path', ''))).name}")
                    else:
                        error_msg = item.get('error', 'Unknown error')
                        self._append_status(f"  ✗ {item.get('set_code', 'unknown')}: {error_msg}")

                # Log warnings
                if warning_items:
                    self._append_status("")
                    self._append_status("Warnings:")
                    for warning in warning_items:
                        self._append_status(f"  ! {warning}")

                # Summary for status tab
                lines = [
                    f"{'Success' if result_status == 'success' else 'Partial success'}: batch complete",
                    f"Sets: {success_count}/{set_count} succeeded",
                    f"Failed: {error_count}",
                    f"Output base: {self.output_path}",
                ]

                # Log final timing
                self._append_status("")
                if self.generation_start_time:
                    elapsed = time.time() - self.generation_start_time
                    self._append_status(f"Total time: {elapsed:.1f}s")
                    lines.append(f"Time: {elapsed:.1f}s")
                
                status_msg = "\n".join(lines)
                self._set_status(status_msg)
                
                # Show main result dialog
                if result_status == "success":
                    messagebox.showinfo("Success", status_msg)
                else:
                    messagebox.showwarning("Partial Success", status_msg)

                # Then show separate warnings dialog if there are warnings
                if warning_items:
                    warning_message = "\n\n".join(warning_items)
                    messagebox.showwarning("Generation Warnings", warning_message)

            else:
                error_msg = str(result.get("error", "Unknown error"))
                self._append_status("")
                self._append_status(f"✗ Error: {error_msg}")
                self._set_status(f"✗ Error:\n{error_msg}")
                messagebox.showerror("Error", error_msg)

        except Exception as e:
            self._append_status("")
            self._append_status(f"✗ Exception: {str(e)}")
            self._set_status(f"✗ Exception:\n{str(e)}")
            messagebox.showerror("Error", str(e))

        finally:
            self.is_generating = False
            self.generate_btn.config(state="normal")
            self.generation_start_time = None

    def _on_open_folder_click(self) -> None:
        """Handle Open Folder button click."""
        if not self.output_path:
            messagebox.showwarning("No Path", "Please generate flashcards first.")
            return

        path = Path(self.output_path)
        if not path.exists():
            messagebox.showerror("Path Not Found", f"Path does not exist: {path}")
            return

        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(path)], check=False)
            else:  # Linux
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def _append_status(self, message: str) -> None:
        """Append to status box."""
        self.status_text.config(state="normal")
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state="disabled")
        self.root.update()

    def _set_status(self, message: str) -> None:
        """Set status box content."""
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(1.0, message)
        self.status_text.config(state="disabled")

    def _setup_keyboard_shortcuts(self) -> None:
        """Register keyboard shortcuts."""
        self.root.bind("<Control-g>", lambda e: self._on_generate_click())
        self.root.bind("<Control-o>", lambda e: self._on_open_folder_click())

    def _on_clear_output(self) -> None:
        """Clear output folder with confirmation."""
        output_path = Path(self.output_var.get()).resolve()
        if not output_path.exists():
            messagebox.showwarning("Folder Not Found", f"Output folder does not exist: {output_path}")
            return

        child_paths = list(output_path.iterdir())
        file_count = sum(1 for path in output_path.rglob("*") if path.is_file())
        dir_count = sum(1 for path in output_path.rglob("*") if path.is_dir())

        if not child_paths:
            messagebox.showinfo("Already Clear", f"No generated files or folders found in {output_path}")
            return

        response = messagebox.askyesno(
            "Clear Output Folder",
            f"Delete all generated contents in:\n{output_path}?\n\n"
            f"Files: {file_count}\nFolders: {dir_count}\n\n"
            "This will remove set folders, README files, and generated images.\n"
            "This cannot be undone.",
        )
        if response:
            try:
                for child_path in child_paths:
                    if child_path.is_dir():
                        shutil.rmtree(child_path)
                    else:
                        child_path.unlink()
                messagebox.showinfo(
                    "Success",
                    f"Deleted {file_count} file(s) and {dir_count} folder(s) from {output_path}.",
                )
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete files: {e}")

    def _validate_colors(self, text_color: str, location_color: str, team_color: str, bg_color: str, text_effect_color: str) -> tuple[bool, str]:
        """Validate color strings using Pillow's parser. Return (is_valid, error_message)."""
        from PIL import ImageColor

        def is_valid_color(color: str) -> bool:
            try:
                ImageColor.getrgb(color)
                return True
            except (ValueError, AttributeError):
                return False

        if not is_valid_color(text_color):
            return False, f"Invalid text color '{text_color}'. Use hex (#RRGGBB) or named color."
        if not is_valid_color(location_color):
            return False, f"Invalid location color '{location_color}'. Use hex (#RRGGBB) or named color."
        if not is_valid_color(team_color):
            return False, f"Invalid team color '{team_color}'. Use hex (#RRGGBB) or named color."
        if not is_valid_color(bg_color):
            return False, f"Invalid background color '{bg_color}'. Use hex (#RRGGBB) or named color."
        if not is_valid_color(text_effect_color):
            return False, f"Invalid effect color '{text_effect_color}'. Use hex (#RRGGBB) or named color."

        return True, ""

    @staticmethod
    def _config_path() -> Path:
        """Return path to the user preferences JSON file."""
        system = platform.system()
        if system == "Windows":
            appdata = os.environ.get("APPDATA")
            base = Path(appdata) if appdata else Path.home()
        elif system == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            xdg = os.environ.get("XDG_CONFIG_HOME")
            base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "SportsFlashcardMaker" / "prefs.json"

    def _load_prefs(self) -> None:
        """Load preferences from config file and apply to UI."""
        path = self._config_path()
        if not path.exists():
            return
        try:
            data: dict = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return

        # Selected sets
        selected = set(data.get("selected_sets", []))
        for code, var in self.set_vars.items():
            var.set(code in selected)

        # General settings
        if "dpi" in data:
            self.dpi_var.set(int(data["dpi"]))
            self.dpi_label.config(text=str(int(data["dpi"])))
        if "card_ratio" in data and data["card_ratio"] in self.RATIO_META:
            self.card_ratio_var.set(data["card_ratio"])
            self._update_ratio_help_label()
        if "output_folder" in data:
            self.output_var.set(data["output_folder"])

        # Card types
        if "card_type_logo" in data:
            self.card_type_logo_var.set(bool(data["card_type_logo"]))
        if "card_type_text" in data:
            self.card_type_text_var.set(bool(data["card_type_text"]))
        if "card_type_combo" in data:
            self.card_type_combo_var.set(bool(data["card_type_combo"]))

        # Naming options
        if "filename_format" in data and data["filename_format"] in ("prefix", "suffix"):
            self.filename_format_var.set(data["filename_format"])
        if "name_format" in data and data["name_format"] in ("full", "team_only", "city_only"):
            self.name_format_var.set(data["name_format"])

        # Text color options
        if "split_text_colors" in data:
            self.split_text_colors_var.set(bool(data["split_text_colors"]))
        if "text_color" in data:
            self.text_color_var.set(data["text_color"])
        if "location_color" in data:
            self.location_color_var.set(data["location_color"])
        if "team_color" in data:
            self.team_color_var.set(data["team_color"])
        if "league_logo_corner" in data and data["league_logo_corner"] in (
            "none", "top-left", "top-right", "bottom-left", "bottom-right"
        ):
            self.league_logo_corner_var.set(data["league_logo_corner"])
        if "text_size" in data and data["text_size"] in ("large", "medium", "small"):
            self.text_size_var.set(data["text_size"])
        if "show_conference" in data:
            self.show_conference_var.set(bool(data["show_conference"]))
        if "abbreviate_conference" in data:
            self.abbreviate_conference_var.set(bool(data["abbreviate_conference"]))
        if "show_abbreviation" in data:
            self.show_abbreviation_var.set(bool(data["show_abbreviation"]))
        if "show_index" in data:
            corner = data["show_index"]
            if corner in ("none", "top-left", "top-right", "bottom-left", "bottom-right"):
                self.index_corner_var.set(corner)
            elif corner is True:
                self.index_corner_var.set("bottom-right")  # migrate old bool pref
        if "index_corner" in data and data["index_corner"] in ("none", "top-left", "top-right", "bottom-left", "bottom-right"):
            self.index_corner_var.set(data["index_corner"])
        if "bg_color" in data:
            self.bg_color_var.set(data["bg_color"])
        if "text_effect" in data and data["text_effect"] in ("none", "shadow", "outline"):
            self.text_effect_var.set(data["text_effect"])
        if "text_effect_color" in data:
            self.text_effect_color_var.set(data["text_effect_color"])
        if "logo_filter" in data and data["logo_filter"] in ("none", "grayscale", "sepia"):
            self.logo_filter_var.set(data["logo_filter"])
        if "pdf_output" in data:
            self.pdf_output_var.set(bool(data["pdf_output"]))

        # Window geometry
        if "geometry" in data:
            try:
                self.root.geometry(data["geometry"])
            except Exception:
                pass

        self._on_name_format_changed()
        self._update_info()

    def _save_prefs(self) -> None:
        """Save current UI state to config file."""
        data = {
            "selected_sets": self._selected_set_codes(),
            "dpi": self.dpi_var.get(),
            "card_ratio": self.card_ratio_var.get(),
            "output_folder": self.output_var.get(),
            "card_type_logo": self.card_type_logo_var.get(),
            "card_type_text": self.card_type_text_var.get(),
            "card_type_combo": self.card_type_combo_var.get(),
            "filename_format": self.filename_format_var.get(),
            "name_format": self.name_format_var.get(),
            "split_text_colors": self.split_text_colors_var.get(),
            "text_color": self.text_color_var.get(),
            "location_color": self.location_color_var.get(),
            "team_color": self.team_color_var.get(),
            "league_logo_corner": self.league_logo_corner_var.get(),
            "text_size": self.text_size_var.get(),
            "show_conference": self.show_conference_var.get(),
            "abbreviate_conference": self.abbreviate_conference_var.get(),
            "show_abbreviation": self.show_abbreviation_var.get(),
            "index_corner": self.index_corner_var.get(),
            "bg_color": self.bg_color_var.get(),
            "text_effect": self.text_effect_var.get(),
            "text_effect_color": self.text_effect_color_var.get(),
            "logo_filter": self.logo_filter_var.get(),
            "pdf_output": self.pdf_output_var.get(),
            "geometry": self.root.geometry(),
        }
        path = self._config_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            if platform.system() != "Windows":
                path.chmod(0o600)
        except Exception:
            pass

    def _on_close(self) -> None:
        """Save preferences then close the window."""
        self._save_prefs()
        self.root.destroy()


def main() -> None:
    """Launch the GUI."""
    root = tk.Tk()
    app = FlashcardGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
