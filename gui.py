"""Smooth desktop UI for the travel planner (CustomTkinter)."""

from __future__ import annotations

import sqlite3
import tkinter.messagebox as messagebox
import threading
from typing import Optional

import customtkinter as ctk

from app_logic import (
    DB_PATH,
    build_itinerary_from_inputs,
    format_itinerary_text,
    initialize_database,
)
from ai_parser import parse_trip_input, ParsedTrip
from planner import recommend_places

_PAD = {"padx": 16, "pady": (8, 4)}

KNOWN_CITIES      = ["Cairo", "Alexandria"]
KNOWN_CATEGORIES  = [
    "attraction", "cafe", "cinema", "dining",
    "hotel", "mall", "museum", "park", "religious", "tour",
]
KNOWN_CATEGORIES_WITH_HOTEL = KNOWN_CATEGORIES  # hotel already included
_SECTION_PAD = {"padx": 16, "pady": (20, 8)}


class TravelPlannerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Travel Planner")
        self.minsize(600, 720)
        self.geometry("900x900")

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self._db_ready = False
        self._build_ui()
        self.after(100, self._init_database_async)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Travel Planner",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        self._status = ctk.CTkLabel(
            header,
            text="Starting…",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray65"),
        )
        self._status.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._tabs = ctk.CTkTabview(self)
        self._tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._tabs.add("✨ Smart Input")
        self._tabs.add("Itinerary")
        self._tabs.add("Recommendations")

        self._build_smart_input_tab()
        self._build_itinerary_tab()
        self._build_recommendations_tab()

    def _build_smart_input_tab(self) -> None:
        tab = self._tabs.tab("✨ Smart Input")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)

        # ── API key row ──────────────────────────────────────────────────────
        key_frame = ctk.CTkFrame(tab, fg_color="transparent")
        key_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        key_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            key_frame,
            text="Groq API Key",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self._api_key_var = ctk.StringVar()
        ctk.CTkEntry(
            key_frame,
            textvariable=self._api_key_var,
            placeholder_text="gsk_…  free key at console.groq.com  (or set GROQ_API_KEY env var)",
            show="*",
            height=32,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=1, sticky="ew")

        # ── Free-text input ──────────────────────────────────────────────────
        ctk.CTkLabel(
            tab,
            text="Describe your trip in plain language",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(12, 4))

        self._smart_input = ctk.CTkTextbox(
            tab,
            height=110,
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            wrap="word",
        )
        self._smart_input.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 4))
        # Placeholder hint
        hint = (
            "e.g.  \"I want to visit Cairo and Alexandria for 5 days. "
            "I love museums and street food. My budget is around 12,000 EGP.\""
        )
        self._smart_input.insert("1.0", hint)
        self._smart_input.bind("<FocusIn>",  self._smart_clear_hint)
        self._smart_input.bind("<FocusOut>", self._smart_restore_hint)
        self._smart_hint_active = True

        # ── Parse button ─────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 8))
        self._parse_btn = ctk.CTkButton(
            btn_row,
            text="✨ Parse & fill itinerary form",
            command=self._on_smart_parse,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
        )
        self._parse_btn.pack(side="left", padx=(0, 10))
        self._parse_spinner = ctk.CTkLabel(
            btn_row,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray65"),
        )
        self._parse_spinner.pack(side="left")

        # ── Result card ───────────────────────────────────────────────────────
        self._smart_result_frame = ctk.CTkFrame(tab, corner_radius=12)
        self._smart_result_frame.grid(
            row=4, column=0, sticky="nsew", padx=16, pady=(0, 16)
        )
        self._smart_result_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            self._smart_result_frame,
            text="Parsed result",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray35", "gray60"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))

        self._smart_summary_label = ctk.CTkLabel(
            self._smart_result_frame,
            text="—",
            font=ctk.CTkFont(size=13),
            wraplength=560,
            justify="left",
        )
        self._smart_summary_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 6))

        # Parsed field badges
        badges = ctk.CTkFrame(self._smart_result_frame, fg_color="transparent")
        badges.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))
        self._badge_cities   = self._make_badge(badges, "🏙 Cities",     col=0)
        self._badge_budget   = self._make_badge(badges, "💰 Budget",     col=1)
        self._badge_days     = self._make_badge(badges, "📅 Days",       col=2)
        self._badge_prefs    = self._make_badge(badges, "⭐ Interests",  col=3)

        ctk.CTkButton(
            self._smart_result_frame,
            text="→ Apply & go to Itinerary tab",
            command=self._on_smart_apply,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            state="disabled",
        ).grid(row=3, column=0, sticky="w", padx=14, pady=(0, 12))
        # Store reference so we can enable it after a successful parse
        self._apply_btn = self._smart_result_frame.winfo_children()[-1]
        self._last_parsed: Optional[ParsedTrip] = None

    def _make_badge(self, parent: ctk.CTkFrame, label: str, col: int) -> ctk.CTkLabel:
        f = ctk.CTkFrame(parent, corner_radius=8, fg_color=("gray85", "gray25"))
        f.grid(row=0, column=col, padx=(0, 8), pady=4, sticky="w")
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10), text_color=("gray40","gray60")).pack(padx=8, pady=(4, 0))
        val = ctk.CTkLabel(f, text="—", font=ctk.CTkFont(size=12, weight="bold"))
        val.pack(padx=8, pady=(0, 4))
        return val

    def _smart_clear_hint(self, _event=None) -> None:
        if self._smart_hint_active:
            self._smart_input.delete("1.0", "end")
            self._smart_input.configure(text_color=("gray10", "gray90"))
            self._smart_hint_active = False

    def _smart_restore_hint(self, _event=None) -> None:
        if not self._smart_input.get("1.0", "end").strip():
            hint = (
                "e.g.  \"I want to visit Cairo and Alexandria for 5 days. "
                "I love museums and street food. My budget is around 12,000 EGP.\""
            )
            self._smart_input.insert("1.0", hint)
            self._smart_input.configure(text_color=("gray50", "gray50"))
            self._smart_hint_active = True

    def _on_smart_parse(self) -> None:
        if self._smart_hint_active:
            messagebox.showwarning("Input", "Please describe your trip first.")
            return
        text = self._smart_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Input", "Please describe your trip first.")
            return

        self._parse_btn.configure(state="disabled")
        self._parse_spinner.configure(text="⏳ Parsing…")
        self._apply_btn.configure(state="disabled")
        self._last_parsed = None

        api_key = self._api_key_var.get().strip() or None

        def worker():
            result = parse_trip_input(text, api_key=api_key)
            self.after(0, lambda: self._on_parse_done(result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_parse_done(self, result: ParsedTrip) -> None:
        self._parse_btn.configure(state="normal")
        if not result.used_fallback:
            spinner_text = "✅ Done (Groq / Llama 3)"
        elif result.fallback_reason == "No API key provided":
            spinner_text = "⚠️ No API key — offline mode"
        else:
            spinner_text = f"⚠️ Offline fallback: {result.fallback_reason}"
        self._parse_spinner.configure(text=spinner_text)
        self._last_parsed = result

        # Update summary label
        self._smart_summary_label.configure(text=result.raw_summary or "Parsing complete.")

        # Update badges
        self._badge_cities.configure(text=", ".join(result.cities) or "Cairo")
        budget_str = f"{result.budget_level.capitalize()} ({result.budget_egp:,} EGP)"
        self._badge_budget.configure(text=budget_str)
        self._badge_days.configure(text=str(result.num_days))
        prefs = ", ".join(result.preferences) if result.preferences else "None"
        self._badge_prefs.configure(text=prefs)

        self._apply_btn.configure(state="normal")

    def _on_smart_apply(self) -> None:
        if self._last_parsed is None:
            return
        p = self._last_parsed
        self._cities_var.set(", ".join(p.cities))
        self._budget_var.set(str(p.budget_egp))
        self._days_var.set(str(p.num_days))
        self._tabs.set("Itinerary")

    def _toggle_city(self, city: str) -> None:
        if city in self._selected_cities:
            self._selected_cities.remove(city)
            self._city_chips[city].configure(
                fg_color=("gray80", "gray30"),
                text_color=("gray20", "gray90"),
            )
        else:
            self._selected_cities.append(city)
            self._city_chips[city].configure(
                fg_color=("#1a6eb5", "#1a4a7a"),
                text_color="white",
            )
        self._cities_var.set(", ".join(self._selected_cities))

    def _build_itinerary_tab(self) -> None:
        tab = self._tabs.tab("Itinerary")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            tab,
            text="Select Cities",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", **_PAD)

        # City chip buttons
        self._cities_var = ctk.StringVar(value="")
        self._selected_cities: list = []
        city_chip_frame = ctk.CTkFrame(tab, fg_color="transparent")
        city_chip_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        self._city_chips: dict = {}
        for i, city in enumerate(KNOWN_CITIES):
            btn = ctk.CTkButton(
                city_chip_frame,
                text=city,
                width=120,
                height=34,
                corner_radius=17,
                fg_color=("gray80", "gray30"),
                text_color=("gray20", "gray90"),
                hover_color=("#1a6eb5", "#1a4a7a"),
                font=ctk.CTkFont(size=13),
                command=lambda c=city: self._toggle_city(c),
            )
            btn.pack(side="left", padx=(0, 8))
            self._city_chips[city] = btn
        # Select Cairo by default
        self._toggle_city("Cairo")

        row = 2
        row_frame = ctk.CTkFrame(tab, fg_color="transparent")
        row_frame.grid(row=row, column=0, sticky="ew", **_SECTION_PAD)
        row_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            row_frame, text="Budget (EGP)", font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4))
        self._budget_var = ctk.StringVar(value="8000")
        ctk.CTkEntry(
            row_frame,
            textvariable=self._budget_var,
            placeholder_text="8000",
            height=36,
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(
            row_frame, text="Days", font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 4))
        self._days_var = ctk.StringVar(value="3")
        ctk.CTkEntry(
            row_frame,
            textvariable=self._days_var,
            placeholder_text="3",
            height=36,
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=1, sticky="ew", padx=(8, 0))

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=16, pady=12)
        ctk.CTkButton(
            btn_row,
            text="Generate itinerary",
            command=self._on_generate_itinerary,
            height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=10,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row,
            text="Clear output",
            command=self._clear_itinerary_output,
            height=40,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90"),
        ).pack(side="left")

        # Scrollable output panel
        self._itinerary_scroll = ctk.CTkScrollableFrame(
            tab,
            corner_radius=12,
            fg_color=("gray92", "gray14"),
        )
        self._itinerary_scroll.grid(row=4, column=0, sticky="nsew", padx=16, pady=(8, 16))
        self._itinerary_scroll.grid_columnconfigure(0, weight=1)

    def _build_recommendations_tab(self) -> None:
        tab = self._tabs.tab("Recommendations")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab,
            text="City & Category",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", **_PAD)
        g = ctk.CTkFrame(tab, fg_color="transparent")
        g.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        g.grid_columnconfigure((0, 1), weight=1)
        self._rec_city = ctk.StringVar(value="Cairo")
        self._rec_cat  = ctk.StringVar(value="museum")
        ctk.CTkOptionMenu(
            g,
            variable=self._rec_city,
            values=KNOWN_CITIES,
            height=36,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkOptionMenu(
            g,
            variable=self._rec_cat,
            values=KNOWN_CATEGORIES,
            height=36,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ctk.CTkLabel(
            tab,
            text="Filters",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=2, column=0, sticky="w", **_SECTION_PAD)

        filter_frame = ctk.CTkFrame(tab, fg_color="transparent")
        filter_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 4))
        filter_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Min price filter
        ctk.CTkLabel(
            filter_frame, text="Min Price (EGP)",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._rec_minp = ctk.StringVar()
        ctk.CTkEntry(
            filter_frame,
            textvariable=self._rec_minp,
            placeholder_text="e.g. 100",
            height=34,
        ).grid(row=1, column=0, sticky="ew", padx=(0, 6))

        # Max price filter
        ctk.CTkLabel(
            filter_frame, text="Max Price (EGP)",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self._rec_maxp = ctk.StringVar()
        ctk.CTkEntry(
            filter_frame,
            textvariable=self._rec_maxp,
            placeholder_text="e.g. 500",
            height=34,
        ).grid(row=1, column=1, sticky="ew", padx=6)

        # Min rating filter
        ctk.CTkLabel(
            filter_frame, text="Min Rating  ★",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=2, sticky="w", pady=(0, 4))
        self._rec_minr = ctk.StringVar(value="Any")
        ctk.CTkOptionMenu(
            filter_frame,
            variable=self._rec_minr,
            values=["Any", "3.0", "3.5", "4.0", "4.2", "4.5", "4.8"],
            height=34,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        ).grid(row=1, column=2, sticky="ew", padx=(6, 0))

        ctk.CTkLabel(
            tab,
            text="Sort by",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=4, column=0, sticky="w", **_SECTION_PAD)

        sort_frame = ctk.CTkFrame(tab, fg_color="transparent")
        sort_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 4))
        sort_frame.grid_columnconfigure((0, 1), weight=1)

        self._sort_by_var = ctk.StringVar(value="rating")
        self._sort_dir_var = ctk.StringVar(value="High → Low")

        ctk.CTkLabel(
            sort_frame, text="Sort Field",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        ctk.CTkOptionMenu(
            sort_frame,
            variable=self._sort_by_var,
            values=["rating", "price"],
            height=34,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        ).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(
            sort_frame, text="Direction",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        ctk.CTkOptionMenu(
            sort_frame,
            variable=self._sort_dir_var,
            values=["High → Low", "Low → High"],
            height=34,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        ).grid(row=1, column=1, sticky="ew", padx=(8, 0))

        # Hidden vars kept for compat with _on_recommend
        self._rec_pbudget = ctk.StringVar()
        self._rw_var = ctk.DoubleVar(value=1.0)
        self._pw_var = ctk.DoubleVar(value=1.0)

        ctk.CTkButton(
            tab,
            text="Get recommendations",
            command=self._on_recommend,
            height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
        ).grid(row=6, column=0, sticky="ew", padx=16, pady=(12, 8))

        self._rec_scroll = ctk.CTkScrollableFrame(
            tab,
            corner_radius=12,
            fg_color=("gray92", "gray14"),
        )
        self._rec_scroll.grid(row=7, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._rec_scroll.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(7, weight=1)
        tab.grid_columnconfigure(0, weight=1)

    def _init_database_async(self) -> None:
        try:
            initialize_database()
        except sqlite3.Error as exc:
            self._status.configure(
                text=f"Database error: {exc}",
                text_color="#c0392b",
            )
            messagebox.showerror(
                "Database",
                f"Could not initialize database at {DB_PATH}:\n{exc}",
            )
            return
        self._db_ready = True
        self._status.configure(
            text="Database ready",
            text_color=("gray40", "gray65"),
        )

    # ── category icons ──────────────────────────────────────────────────────
    _CAT_ICON = {
        "museum":     "🏛",
        "attraction": "🗺",
        "religious":  "🕌",
        "cinema":     "🎬",
        "mall":       "🛍",
        "cafe":       "☕",
        "dining":     "🍽",
        "park":       "🌳",
        "tour":       "🚌",
        "hotel":      "🏨",
    }

    def _clear_itinerary_output(self) -> None:
        for w in self._itinerary_scroll.winfo_children():
            w.destroy()

    def _on_generate_itinerary(self) -> None:
        if not self._db_ready:
            messagebox.showwarning("Please wait", "Database is still initializing.")
            return
        itinerary, err = build_itinerary_from_inputs(
            self._cities_var.get(),
            self._budget_var.get(),
            self._days_var.get(),
        )
        self._clear_itinerary_output()
        if err:
            ctk.CTkLabel(
                self._itinerary_scroll,
                text=f"⚠  {err}",
                font=ctk.CTkFont(size=13),
                text_color="#e74c3c",
                wraplength=600,
                justify="left",
            ).grid(row=0, column=0, sticky="w", padx=16, pady=16)
            return
        assert itinerary is not None
        self._render_itinerary(itinerary)

    def _render_itinerary(self, itinerary) -> None:
        """Render day cards into the scrollable frame."""
        scroll = self._itinerary_scroll
        row_idx = 0
        current_city = ""
        grand_total = sum(d.total_cost for d in itinerary)
        total_days  = len(itinerary)

        # ── Trip summary bar ────────────────────────────────────────────────
        summary_bar = ctk.CTkFrame(scroll, corner_radius=10,
                                   fg_color=("gray85", "gray20"))
        summary_bar.grid(row=row_idx, column=0, sticky="ew",
                         padx=12, pady=(12, 6))
        summary_bar.grid_columnconfigure((0, 1, 2), weight=1)
        row_idx += 1

        cities_shown = ", ".join(
            dict.fromkeys(getattr(d, "city", "") for d in itinerary if getattr(d, "city", ""))
        )
        for col, (icon, label, val) in enumerate([
            ("📍", "Cities",     cities_shown or "—"),
            ("📅", "Total days", str(total_days)),
            ("💰", "Total cost", f"{grand_total:,} EGP"),
        ]):
            f = ctk.CTkFrame(summary_bar, fg_color="transparent")
            f.grid(row=0, column=col, padx=16, pady=10, sticky="ew")
            ctk.CTkLabel(f, text=f"{icon}  {label}",
                         font=ctk.CTkFont(size=11),
                         text_color=("gray40", "gray60")).pack(anchor="w")
            ctk.CTkLabel(f, text=val,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")

        # ── Day cards ────────────────────────────────────────────────────────
        for day in itinerary:
            city = getattr(day, "city", "")

            # City header when city changes
            if city and city != current_city:
                current_city = city
                city_hdr = ctk.CTkFrame(scroll, corner_radius=8,
                                        fg_color=("#1a6eb5", "#1a4a7a"))
                city_hdr.grid(row=row_idx, column=0, sticky="ew",
                              padx=12, pady=(14, 4))
                row_idx += 1
                ctk.CTkLabel(
                    city_hdr,
                    text=f"📍  {city.upper()}",
                    font=ctk.CTkFont(size=15, weight="bold"),
                    text_color="white",
                ).pack(side="left", padx=14, pady=8)

            # Day card
            card = ctk.CTkFrame(scroll, corner_radius=10,
                                fg_color=("white", "gray17"),
                                border_width=1,
                                border_color=("gray80", "gray30"))
            card.grid(row=row_idx, column=0, sticky="ew",
                      padx=12, pady=4)
            card.grid_columnconfigure(0, weight=1)
            row_idx += 1

            # Card header
            hdr = ctk.CTkFrame(card, corner_radius=0,
                               fg_color=("gray88", "gray22"))
            hdr.grid(row=0, column=0, sticky="ew",
                     padx=0, pady=0)
            hdr.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                hdr,
                text=f"  Day {day.day_number}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("#1a6eb5", "#4da6ff"),
            ).grid(row=0, column=0, sticky="w", padx=(10, 4), pady=6)

            ctk.CTkLabel(
                hdr,
                text=f"{len(day.places)} stops",
                font=ctk.CTkFont(size=11),
                text_color=("gray45", "gray55"),
            ).grid(row=0, column=1, sticky="w", padx=4, pady=6)

            ctk.CTkLabel(
                hdr,
                text=f"{day.total_cost:,} EGP  ",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("#27ae60", "#2ecc71"),
            ).grid(row=0, column=2, sticky="e", padx=(4, 10), pady=6)

            # Place rows
            for p_idx, place in enumerate(day.places):
                icon = self._CAT_ICON.get(place.category, "📌")
                row_bg = ("gray96", "gray19") if p_idx % 2 == 0 else ("white", "gray17")

                prow = ctk.CTkFrame(card, corner_radius=0, fg_color=row_bg)
                prow.grid(row=p_idx + 1, column=0, sticky="ew", padx=0, pady=0)
                prow.grid_columnconfigure(1, weight=1)

                # Icon + name
                ctk.CTkLabel(
                    prow,
                    text=f"  {icon}",
                    font=ctk.CTkFont(size=15),
                    width=30,
                ).grid(row=0, column=0, padx=(10, 4), pady=5, sticky="w")

                ctk.CTkLabel(
                    prow,
                    text=place.name,
                    font=ctk.CTkFont(size=13),
                    anchor="w",
                ).grid(row=0, column=1, padx=4, pady=5, sticky="ew")

                # Category tag
                ctk.CTkLabel(
                    prow,
                    text=place.category,
                    font=ctk.CTkFont(size=10),
                    text_color=("gray50", "gray55"),
                    fg_color=("gray85", "gray28"),
                    corner_radius=4,
                    padx=6, pady=2,
                ).grid(row=0, column=2, padx=6, pady=5)

                # Rating
                ctk.CTkLabel(
                    prow,
                    text=f"★ {place.rating}",
                    font=ctk.CTkFont(size=11),
                    text_color=("#e67e22", "#f39c12"),
                    width=50,
                ).grid(row=0, column=3, padx=4, pady=5)

                # Price
                price_text = "Free" if place.price == 0 else f"{place.price:,} EGP"
                ctk.CTkLabel(
                    prow,
                    text=f"{price_text}  ",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=("#27ae60", "#2ecc71") if place.price == 0
                               else ("gray20", "gray90"),
                    width=90,
                    anchor="e",
                ).grid(row=0, column=4, padx=(4, 10), pady=5)

        # ── Grand total footer ───────────────────────────────────────────────
        footer = ctk.CTkFrame(scroll, corner_radius=10,
                              fg_color=("#27ae60", "#1e8449"))
        footer.grid(row=row_idx, column=0, sticky="ew", padx=12, pady=(10, 14))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            footer,
            text=f"🧾  Trip Total:  {grand_total:,} EGP   across {total_days} days",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
        ).grid(row=0, column=0, pady=10)

    def _clear_rec_output(self) -> None:
        for w in self._rec_scroll.winfo_children():
            w.destroy()

    def _on_recommend(self) -> None:
        if not self._db_ready:
            messagebox.showwarning("Please wait", "Database is still initializing.")
            return
        city = self._rec_city.get().strip()
        cat = self._rec_cat.get().strip()
        if not city or not cat:
            messagebox.showwarning("Input", "Enter both city and category.")
            return

        max_price: Optional[int] = None
        s = self._rec_maxp.get().strip()
        if s:
            try:
                max_price = int(float(s))
            except ValueError:
                messagebox.showerror("Input", "Max price must be a number.")
                return

        min_rating: Optional[float] = None
        s = self._rec_minr.get().strip()
        if s and s != "Any":
            try:
                min_rating = float(s)
            except ValueError:
                pass

        price_budget: Optional[float] = None
        s = self._rec_pbudget.get().strip()
        if s:
            try:
                price_budget = float(s)
            except ValueError:
                messagebox.showerror("Input", "Price budget must be a number.")
                return

        min_price: Optional[int] = None
        s = self._rec_minp.get().strip()
        if s:
            try:
                min_price = int(float(s))
            except ValueError:
                messagebox.showerror("Input", "Min price must be a number.")
                return

        sort_by    = self._sort_by_var.get()
        descending = self._sort_dir_var.get() == "High → Low"

        self._clear_rec_output()
        try:
            from database import get_places_filtered
            places = get_places_filtered(
                city=city,
                category=cat,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating,
                sort_by=sort_by,
                descending=descending,
                limit=12,
            )
        except ValueError as exc:
            ctk.CTkLabel(
                self._rec_scroll,
                text=f"⚠  {exc}",
                font=ctk.CTkFont(size=13),
                text_color="#e74c3c",
            ).grid(row=0, column=0, sticky="w", padx=16, pady=16)
            return

        if not places:
            ctk.CTkLabel(
                self._rec_scroll,
                text="😕  No places matched your filters.",
                font=ctk.CTkFont(size=13),
                text_color=("gray40", "gray60"),
            ).grid(row=0, column=0, sticky="w", padx=16, pady=16)
            return

        self._render_recommendations(places, city, cat)

    def _render_recommendations(self, places, city: str, cat: str) -> None:
        """Render recommendation result cards into the scrollable frame."""
        scroll = self._rec_scroll
        row_idx = 0

        # ── Results header bar ───────────────────────────────────────────────
        hdr_bar = ctk.CTkFrame(scroll, corner_radius=10,
                               fg_color=("#1a6eb5", "#1a4a7a"))
        hdr_bar.grid(row=row_idx, column=0, sticky="ew", padx=12, pady=(12, 8))
        hdr_bar.grid_columnconfigure(0, weight=1)
        row_idx += 1

        icon = self._CAT_ICON.get(cat.lower(), "📌")
        ctk.CTkLabel(
            hdr_bar,
            text=f"{icon}  {cat.capitalize()} recommendations in {city}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="white",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=8)
        ctk.CTkLabel(
            hdr_bar,
            text=f"{len(places)} results  ",
            font=ctk.CTkFont(size=12),
            text_color=("gray80", "gray70"),
        ).grid(row=0, column=1, sticky="e", padx=14, pady=8)

        # ── Place cards ──────────────────────────────────────────────────────
        free_count  = sum(1 for p in places if p.price == 0)
        avg_rating  = sum(p.rating for p in places) / len(places)
        avg_price   = sum(p.price for p in places if p.price > 0)
        paid_count  = len(places) - free_count
        avg_price_val = (avg_price // paid_count) if paid_count else 0

        for idx, place in enumerate(places):
            card = ctk.CTkFrame(scroll, corner_radius=10,
                                fg_color=("white", "gray17"),
                                border_width=1,
                                border_color=("gray80", "gray30"))
            card.grid(row=row_idx, column=0, sticky="ew", padx=12, pady=4)
            card.grid_columnconfigure(1, weight=1)
            row_idx += 1

            # Rank badge
            rank_color = ("#f39c12", "#e67e22") if idx == 0 else                          ("#95a5a6", "#7f8c8d") if idx == 1 else                          ("#cd7f32", "#a0522d") if idx == 2 else                          ("gray70", "gray45")
            rank_frame = ctk.CTkFrame(card, corner_radius=8,
                                      fg_color=rank_color, width=36, height=36)
            rank_frame.grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=10, sticky="n")
            rank_frame.grid_propagate(False)
            ctk.CTkLabel(
                rank_frame,
                text=f"#{idx + 1}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white",
            ).place(relx=0.5, rely=0.5, anchor="center")

            # Name & city
            ctk.CTkLabel(
                card,
                text=place.name,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(10, 0))

            ctk.CTkLabel(
                card,
                text=f"📍 {place.city}",
                font=ctk.CTkFont(size=11),
                text_color=("gray45", "gray55"),
                anchor="w",
            ).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(0, 10))

            # Rating bar (visual stars)
            stars_filled = round(place.rating)
            stars_str = "★" * stars_filled + "☆" * (5 - stars_filled)
            rating_frame = ctk.CTkFrame(card, fg_color="transparent")
            rating_frame.grid(row=0, column=2, rowspan=2, padx=(0, 8), pady=10, sticky="e")

            ctk.CTkLabel(
                rating_frame,
                text=stars_str,
                font=ctk.CTkFont(size=13),
                text_color=("#e67e22", "#f39c12"),
            ).pack(anchor="e")
            ctk.CTkLabel(
                rating_frame,
                text=f"{place.rating} / 5.0",
                font=ctk.CTkFont(size=10),
                text_color=("gray45", "gray55"),
            ).pack(anchor="e")

            # Price badge
            price_text = "FREE" if place.price == 0 else f"{place.price:,} EGP"
            price_color = ("#27ae60", "#2ecc71") if place.price == 0                           else ("#2980b9", "#3498db")
            price_badge = ctk.CTkFrame(card, corner_radius=8,
                                       fg_color=price_color)
            price_badge.grid(row=0, column=3, rowspan=2,
                             padx=(0, 12), pady=10, sticky="e")
            ctk.CTkLabel(
                price_badge,
                text=f"  {price_text}  ",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white",
            ).pack(padx=4, pady=6)

        # ── Summary footer ───────────────────────────────────────────────────
        footer = ctk.CTkFrame(scroll, corner_radius=10,
                              fg_color=("gray85", "gray20"))
        footer.grid(row=row_idx, column=0, sticky="ew", padx=12, pady=(8, 14))
        footer.grid_columnconfigure((0, 1, 2), weight=1)

        for col, (ico, lbl, val) in enumerate([
            ("🔢", "Results",    str(len(places))),
            ("★",  "Avg rating", f"{avg_rating:.1f} / 5.0"),
            ("💰", "Avg price",  "Free" if avg_price_val == 0 else f"{avg_price_val:,} EGP"),
        ]):
            sf = ctk.CTkFrame(footer, fg_color="transparent")
            sf.grid(row=0, column=col, padx=16, pady=10, sticky="ew")
            ctk.CTkLabel(sf, text=f"{ico}  {lbl}",
                         font=ctk.CTkFont(size=11),
                         text_color=("gray40", "gray60")).pack(anchor="w")
            ctk.CTkLabel(sf, text=val,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")


def main() -> None:
    app = TravelPlannerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
