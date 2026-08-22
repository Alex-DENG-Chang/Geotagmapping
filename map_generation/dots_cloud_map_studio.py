#!/usr/bin/env python3
"""
Photo GPS Map Studio
====================

Interactive Folium map designer with a live browser preview and modern GUI.

Run:
    python dots_cloud_map_studio.py
"""

import os
import tempfile
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

import folium
from folium.plugins import HeatMap, MarkerCluster, MiniMap, Fullscreen, MousePosition
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CSV = "/Users/alexdengmbp21/🧑‍💻_python_projets/heatmap/csv/photo_gps_data.csv"
DEFAULT_OUTPUT = "photo_gps_map.html"

MAP_PROVIDERS = {
    "OpenStreetMap": {
        "tiles": "OpenStreetMap",
        "attr": "© OpenStreetMap contributors",
    },
    "CartoDB Positron": {
        "tiles": "CartoDB positron",
        "attr": "© OpenStreetMap contributors © CARTO",
    },
    "CartoDB Dark Matter": {
        "tiles": "CartoDB dark_matter",
        "attr": "© OpenStreetMap contributors © CARTO",
    },
    "CartoDB Voyager": {
        "tiles": "CartoDB Voyager",
        "attr": "© OpenStreetMap contributors © CARTO",
    },
    "Esri WorldStreetMap": {
        "tiles": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
        ),
        "attr": "Tiles © Esri",
    },
    "Esri WorldImagery": {
        "tiles": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        "attr": "Tiles © Esri",
    },
    "Esri WorldTopoMap": {
        "tiles": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
        ),
        "attr": "Tiles © Esri",
    },
}

HEAT_GRADIENTS = {
    "Classic": {
        0.0: "blue",
        0.25: "cyan",
        0.5: "lime",
        0.75: "yellow",
        1.0: "red",
    },
    "Warm": {
        0.0: "purple",
        0.25: "blue",
        0.5: "orange",
        0.75: "red",
        1.0: "white",
    },
    "Fire": {
        0.0: "black",
        0.25: "purple",
        0.5: "red",
        0.75: "orange",
        1.0: "yellow",
    },
    "Cool": {
        0.0: "navy",
        0.25: "blue",
        0.5: "cyan",
        0.75: "white",
        1.0: "yellow",
    },
    "Ocean": {
        0.0: "black",
        0.25: "navy",
        0.5: "blue",
        0.75: "cyan",
        1.0: "white",
    },
}


# ---------------------------------------------------------------------------
# Modern Theme Palette
# ---------------------------------------------------------------------------

BG_DARK = "#0f172a"          # Slate 900
BG_CARD = "#1e293b"          # Slate 800
BG_CARD_LIGHT = "#334155"    # Slate 700
ACCENT_BLUE = "#3b82f6"      # Blue 500
ACCENT_BLUE_HOVER = "#2563eb"# Blue 600
ACCENT_GREEN = "#10b981"     # Emerald 500
ACCENT_GREEN_HOVER = "#059669"# Emerald 600
TEXT_LIGHT = "#f8fafc"       # Slate 50
TEXT_MUTED = "#94a3b8"       # Slate 400
TEXT_ACCENT = "#38bdf8"      # Sky 400


# ---------------------------------------------------------------------------
# Application Class
# ---------------------------------------------------------------------------

class MapStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("🗺️ Photo GPS Map Studio")
        self.root.geometry("1180x800")
        self.root.minsize(1020, 680)
        self.root.configure(bg=BG_DARK)

        self.df = None
        self.last_preview_path = None
        self.selected_color = "#3186cc"

        # General Variables
        self.csv_var = tk.StringVar(value=DEFAULT_CSV)
        self.output_var = tk.StringVar(value=DEFAULT_OUTPUT)
        self.visualization_var = tk.StringVar(value="Dots")
        self.provider_var = tk.StringVar(value="CartoDB Positron")
        self.lat_var = tk.StringVar()
        self.lon_var = tk.StringVar()

        self.zoom_var = tk.IntVar(value=3)
        self.fit_bounds_var = tk.BooleanVar(value=True)

        # Dots Variables
        self.dot_radius_var = tk.IntVar(value=5)
        self.dot_opacity_var = tk.DoubleVar(value=0.60)
        self.dot_outline_var = tk.BooleanVar(value=False)
        self.dot_weight_var = tk.IntVar(value=1)
        self.cluster_var = tk.BooleanVar(value=False)

        # Heatmap Variables
        self.heat_radius_var = tk.IntVar(value=20)
        self.heat_blur_var = tk.IntVar(value=15)
        self.heat_min_opacity_var = tk.DoubleVar(value=0.15)
        self.heat_max_opacity_var = tk.DoubleVar(value=0.85)
        self.heat_gradient_var = tk.StringVar(value="Classic")
        self.heat_max_zoom_var = tk.IntVar(value=18)
        self.weight_visits_var = tk.BooleanVar(value=False)
        self.merge_duplicates_var = tk.BooleanVar(value=False)

        # Presentation Variables
        self.fullscreen_var = tk.BooleanVar(value=True)
        self.scale_var = tk.BooleanVar(value=True)
        self.mouse_position_var = tk.BooleanVar(value=True)
        self.minimap_var = tk.BooleanVar(value=False)
        self.layer_control_var = tk.BooleanVar(value=True)
        self.open_after_var = tk.BooleanVar(value=True)

        self.apply_styles()
        self.build_ui()
        self.setup_slider_traces()
        self.load_csv(silent=True)

    # ------------------------------------------------------------------
    # Styling & Layout
    # ------------------------------------------------------------------

    def apply_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=BG_DARK, foreground=TEXT_LIGHT, font=("Segoe UI", 9))
        style.configure("TFrame", background=BG_DARK)
        style.configure("Card.TFrame", background=BG_CARD, relief="flat")
        style.configure("Header.TFrame", background=BG_CARD)

        # Labels
        style.configure("TLabel", background=BG_CARD, foreground=TEXT_LIGHT)
        style.configure("Title.TLabel", background=BG_CARD, foreground=TEXT_LIGHT, font=("Segoe UI", 16, "bold"))
        style.configure("Subtitle.TLabel", background=BG_CARD, foreground=TEXT_MUTED, font=("Segoe UI", 9))
        style.configure("Muted.TLabel", background=BG_CARD, foreground=TEXT_MUTED, font=("Segoe UI", 9))
        style.configure("Section.TLabel", background=BG_CARD, foreground=TEXT_ACCENT, font=("Segoe UI", 10, "bold"))

        # Label Frames
        style.configure(
            "TLabelframe",
            background=BG_CARD,
            bordercolor=BG_CARD_LIGHT,
            lightcolor=BG_CARD_LIGHT,
            darkcolor=BG_CARD_LIGHT,
            borderwidth=1,
        )
        style.configure(
            "TLabelframe.Label",
            background=BG_CARD,
            foreground=TEXT_ACCENT,
            font=("Segoe UI", 10, "bold"),
        )

        # Buttons
        style.configure(
            "Primary.TButton",
            background=ACCENT_BLUE,
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=(12, 8),
        )
        style.map("Primary.TButton", background=[("active", ACCENT_BLUE_HOVER)])

        style.configure(
            "Success.TButton",
            background=ACCENT_GREEN,
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=(12, 8),
        )
        style.map("Success.TButton", background=[("active", ACCENT_GREEN_HOVER)])

        style.configure(
            "Secondary.TButton",
            background=BG_CARD_LIGHT,
            foreground=TEXT_LIGHT,
            font=("Segoe UI", 9),
            borderwidth=0,
            padding=(8, 4),
        )
        style.map("Secondary.TButton", background=[("active", "#475569")])

        # Notebook (Tabs)
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=BG_CARD,
            foreground=TEXT_MUTED,
            padding=[14, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT_BLUE)],
            foreground=[("selected", "#ffffff")],
        )

        # Form Controls
        style.configure(
            "TCheckbutton",
            background=BG_CARD,
            foreground=TEXT_LIGHT,
            font=("Segoe UI", 9),
        )
        style.map("TCheckbutton", background=[("active", BG_CARD)])

        style.configure(
            "TCombobox",
            fieldbackground=BG_DARK,
            background=BG_CARD_LIGHT,
            foreground=TEXT_LIGHT,
            arrowcolor=TEXT_LIGHT,
            padding=4,
        )
        style.map("TCombobox", fieldbackground=[("readonly", BG_DARK)], foreground=[("readonly", TEXT_LIGHT)])

        style.configure("TEntry", fieldbackground=BG_DARK, foreground=TEXT_LIGHT, insertcolor=TEXT_LIGHT, padding=4)
        style.configure("TSpinbox", fieldbackground=BG_DARK, foreground=TEXT_LIGHT, arrowcolor=TEXT_LIGHT, padding=3)

    def build_ui(self):
        # Header Banner
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(18, 12))
        header.pack(fill="x", side="top")

        title_box = ttk.Frame(header, style="Header.TFrame")
        title_box.pack(side="left")

        ttk.Label(title_box, text="🗺️ Photo GPS Map Studio", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            title_box,
            text="Interactive map designer with live browser updates & customizable density visuals",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        # Main Layout (Left: Controls, Right: Actions & Dashboard)
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=12, pady=12)

        left_frame = ttk.Frame(paned)
        right_frame = ttk.Frame(paned)

        paned.add(left_frame, weight=3)
        paned.add(right_frame, weight=2)

        self.build_tabs(left_frame)
        self.build_dashboard(right_frame)

    def build_tabs(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)

        # Tab 1: Data Source
        tab_data = ttk.Frame(notebook, padding=10)
        notebook.add(tab_data, text=" 📊 Data Source ")
        self.build_data_tab(tab_data)

        # Tab 2: Map & Visuals
        tab_visuals = ttk.Frame(notebook, padding=10)
        notebook.add(tab_visuals, text=" 🎨 Map & Visuals ")
        self.build_visuals_tab(tab_visuals)

        # Tab 3: Controls & Export
        tab_export = ttk.Frame(notebook, padding=10)
        notebook.add(tab_export, text=" ⚙️ Controls & Export ")
        self.build_export_tab(tab_export)

    # ------------------------------------------------------------------
    # Tabs Implementation
    # ------------------------------------------------------------------

    def build_data_tab(self, parent):
        # File Picker Card
        f_file = ttk.LabelFrame(parent, text="1. Select Dataset (CSV)", padding=10)
        f_file.pack(fill="x", pady=(0, 10))
        f_file.columnconfigure(1, weight=1)

        ttk.Label(f_file, text="CSV File:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        ttk.Entry(f_file, textvariable=self.csv_var).grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        ttk.Button(f_file, text="Browse…", style="Secondary.TButton", command=self.browse_csv).grid(
            row=0, column=2, padx=4
        )

        ttk.Button(f_file, text="↻ Reload CSV", style="Secondary.TButton", command=self.load_csv).grid(
            row=1, column=1, sticky="e", padx=5, pady=4
        )

        # Column Mapping Card
        f_cols = ttk.LabelFrame(parent, text="2. GPS Column Mapping", padding=10)
        f_cols.pack(fill="x", pady=5)
        f_cols.columnconfigure(1, weight=1)

        ttk.Label(f_cols, text="Latitude Column:").grid(row=0, column=0, sticky="w", padx=5, pady=6)
        self.lat_combo = ttk.Combobox(f_cols, textvariable=self.lat_var, state="readonly")
        self.lat_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=6)

        ttk.Label(f_cols, text="Longitude Column:").grid(row=1, column=0, sticky="w", padx=5, pady=6)
        self.lon_combo = ttk.Combobox(f_cols, textvariable=self.lon_var, state="readonly")
        self.lon_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=6)

        ttk.Checkbutton(
            f_cols,
            text="Merge identical coordinates into count weighted groups",
            variable=self.merge_duplicates_var,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=(8, 4))

        # Dataset Summary Card
        f_stats = ttk.LabelFrame(parent, text="3. Dataset Inspection", padding=10)
        f_stats.pack(fill="x", pady=(10, 0))

        self.stats_var = tk.StringVar(value="No dataset loaded.")
        ttk.Label(f_stats, textvariable=self.stats_var, style="Muted.TLabel", justify="left").pack(
            anchor="w"
        )

    def build_visuals_tab(self, parent):
        # General Map Settings Card
        f_map = ttk.LabelFrame(parent, text="Map & Base Layer", padding=10)
        f_map.pack(fill="x", pady=(0, 8))
        f_map.columnconfigure(1, weight=1)

        ttk.Label(f_map, text="Visualization Mode:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        combo_mode = ttk.Combobox(
            f_map,
            textvariable=self.visualization_var,
            values=["Dots", "Heatmap", "Dots + Heatmap"],
            state="readonly",
        )
        combo_mode.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        combo_mode.bind("<<ComboboxSelected>>", lambda e: self.refresh_dynamic_sections())

        ttk.Label(f_map, text="Tile Provider:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(
            f_map,
            textvariable=self.provider_var,
            values=list(MAP_PROVIDERS.keys()),
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(f_map, text="Initial Zoom Level:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Spinbox(f_map, from_=1, to=20, textvariable=self.zoom_var, width=6).grid(
            row=2, column=1, sticky="w", padx=5, pady=5
        )

        ttk.Checkbutton(
            f_map,
            text="Automatically zoom & fit bounds to all locations",
            variable=self.fit_bounds_var,
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=4)

        # Dynamic Holder for Dots & Heatmap settings
        self.dynamic_holder = ttk.Frame(parent)
        self.dynamic_holder.pack(fill="both", expand=True)

        self.dot_frame = ttk.LabelFrame(self.dynamic_holder, text="Dots Styling", padding=10)
        self.heat_frame = ttk.LabelFrame(self.dynamic_holder, text="Heatmap Density Styling", padding=10)

        self.build_dot_settings()
        self.build_heat_settings()
        self.refresh_dynamic_sections()

    def build_dot_settings(self):
        f = self.dot_frame
        f.columnconfigure(1, weight=1)

        # Size
        ttk.Label(f, text="Dot Radius:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        ttk.Scale(f, from_=1, to=30, variable=self.dot_radius_var, orient="horizontal").grid(
            row=0, column=1, sticky="ew", padx=5
        )
        self.dot_radius_label = ttk.Label(f, text="5 px", width=6)
        self.dot_radius_label.grid(row=0, column=2)

        # Opacity
        ttk.Label(f, text="Fill Opacity:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ttk.Scale(f, from_=0.05, to=1.0, variable=self.dot_opacity_var, orient="horizontal").grid(
            row=1, column=1, sticky="ew", padx=5
        )
        self.dot_opacity_label = ttk.Label(f, text="0.60", width=6)
        self.dot_opacity_label.grid(row=1, column=2)

        # Color
        ttk.Label(f, text="Fill Color:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        color_row = ttk.Frame(f)
        color_row.grid(row=2, column=1, columnspan=2, sticky="w", padx=5)

        self.color_swatch = tk.Frame(
            color_row, width=28, height=18, bg=self.selected_color, highlightbackground="#334155", highlightthickness=1
        )
        self.color_swatch.pack(side="left", padx=(0, 8))

        self.color_hex_label = ttk.Label(color_row, text=self.selected_color, font=("Segoe UI", 9, "bold"))
        self.color_hex_label.pack(side="left", padx=(0, 10))

        ttk.Button(color_row, text="Choose Color…", style="Secondary.TButton", command=self.choose_color).pack(
            side="left"
        )

        # Outline & Clustering
        ttk.Checkbutton(
            f, text="Enable dot border outline", variable=self.dot_outline_var, command=self.update_outline_state
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=(8, 2))

        ttk.Label(f, text="Outline Width:").grid(row=4, column=0, sticky="w", padx=5, pady=4)
        self.outline_spin = ttk.Spinbox(f, from_=0, to=5, textvariable=self.dot_weight_var, width=6)
        self.outline_spin.grid(row=4, column=1, sticky="w", padx=5)

        ttk.Checkbutton(f, text="Cluster nearby points", variable=self.cluster_var).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=5, pady=(6, 2)
        )

    def build_heat_settings(self):
        f = self.heat_frame
        f.columnconfigure(1, weight=1)

        # Radius & Blur
        ttk.Label(f, text="Heat Radius:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        ttk.Scale(f, from_=5, to=80, variable=self.heat_radius_var, orient="horizontal").grid(
            row=0, column=1, sticky="ew", padx=5
        )
        self.heat_radius_label = ttk.Label(f, text="20 px", width=6)
        self.heat_radius_label.grid(row=0, column=2)

        ttk.Label(f, text="Blur Amount:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ttk.Scale(f, from_=1, to=50, variable=self.heat_blur_var, orient="horizontal").grid(
            row=1, column=1, sticky="ew", padx=5
        )
        self.heat_blur_label = ttk.Label(f, text="15 px", width=6)
        self.heat_blur_label.grid(row=1, column=2)

        # Opacities
        ttk.Label(f, text="Min Opacity:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        ttk.Scale(f, from_=0.0, to=1.0, variable=self.heat_min_opacity_var, orient="horizontal").grid(
            row=2, column=1, sticky="ew", padx=5
        )
        self.heat_min_opacity_label = ttk.Label(f, text="0.15", width=6)
        self.heat_min_opacity_label.grid(row=2, column=2)

        ttk.Label(f, text="Max Opacity:").grid(row=3, column=0, sticky="w", padx=5, pady=4)
        ttk.Scale(f, from_=0.1, to=1.0, variable=self.heat_max_opacity_var, orient="horizontal").grid(
            row=3, column=1, sticky="ew", padx=5
        )
        self.heat_max_opacity_label = ttk.Label(f, text="0.85", width=6)
        self.heat_max_opacity_label.grid(row=3, column=2)

        # Gradient & Max Zoom
        ttk.Label(f, text="Color Gradient:").grid(row=4, column=0, sticky="w", padx=5, pady=4)
        ttk.Combobox(
            f, textvariable=self.heat_gradient_var, values=list(HEAT_GRADIENTS.keys()), state="readonly"
        ).grid(row=4, column=1, sticky="ew", padx=5)

        ttk.Label(f, text="Max Zoom Scale:").grid(row=5, column=0, sticky="w", padx=5, pady=4)
        ttk.Spinbox(f, from_=1, to=22, textvariable=self.heat_max_zoom_var, width=6).grid(
            row=5, column=1, sticky="w", padx=5
        )

        ttk.Checkbutton(
            f, text="Weight heatmap by visit frequency", variable=self.weight_visits_var
        ).grid(row=6, column=0, columnspan=3, sticky="w", padx=5, pady=(6, 2))

    def build_export_tab(self, parent):
        # UI Overlays Card
        f_ui = ttk.LabelFrame(parent, text="Map Control Overlays", padding=10)
        f_ui.pack(fill="x", pady=(0, 10))

        options = [
            ("Fullscreen Toggle Button", self.fullscreen_var),
            ("Scale Bar", self.scale_var),
            ("Live Mouse Coordinates Display", self.mouse_position_var),
            ("Mini-Map Preview Corner", self.minimap_var),
            ("Layer Selection Control", self.layer_control_var),
        ]

        for idx, (text, var) in enumerate(options):
            ttk.Checkbutton(f_ui, text=text, variable=var).grid(
                row=idx // 2, column=idx % 2, sticky="w", padx=6, pady=4
            )

        # Final Export Card
        f_exp = ttk.LabelFrame(parent, text="Final Output Generation", padding=10)
        f_exp.pack(fill="x", pady=5)
        f_exp.columnconfigure(1, weight=1)

        ttk.Label(f_exp, text="Output HTML File:").grid(row=0, column=0, sticky="w", padx=5, pady=6)
        ttk.Entry(f_exp, textvariable=self.output_var).grid(row=0, column=1, sticky="ew", padx=5, pady=6)
        ttk.Button(f_exp, text="Browse…", style="Secondary.TButton", command=self.browse_output).grid(
            row=0, column=2, padx=4
        )

        ttk.Checkbutton(
            f_exp, text="Automatically open final HTML map after generation", variable=self.open_after_var
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=6)

    def build_dashboard(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill="both", expand=True)

        # Primary Actions Box
        ttk.Label(card, text="Quick Actions", style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        btn_row = ttk.Frame(card, style="Card.TFrame")
        btn_row.pack(fill="x", pady=(0, 12))

        ttk.Button(
            btn_row, text="👁️  UPDATE PREVIEW", style="Primary.TButton", command=self.update_preview
        ).pack(fill="x", pady=(0, 6))

        ttk.Button(
            btn_row, text="💾  GENERATE FINAL HTML", style="Success.TButton", command=self.generate_final
        ).pack(fill="x", pady=(0, 6))

        ttk.Button(
            btn_row, text="↗ Open Last Preview in Browser", style="Secondary.TButton", command=self.open_last_preview
        ).pack(fill="x")

        # Preview Workflow Notice
        f_info = ttk.LabelFrame(card, text="Live Preview Workflow", padding=10)
        f_info.pack(fill="x", pady=8)

        ttk.Label(
            f_info,
            text=(
                "The preview creates a fast temporary HTML map in your browser. "
                "Adjust any settings on the left and click 'Update Preview' to instantly refine your design."
            ),
            style="Muted.TLabel",
            wraplength=380,
            justify="left",
        ).pack(anchor="w")

        # Live Console / Event Log
        f_log = ttk.LabelFrame(card, text="Activity Log Console", padding=10)
        f_log.pack(fill="both", expand=True, pady=(8, 0))

        self.log_text = tk.Text(
            f_log,
            height=10,
            wrap="word",
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            insertbackground=TEXT_LIGHT,
            relief="flat",
            font=("Consolas", 9),
            highlightthickness=0,
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scroll = ttk.Scrollbar(f_log, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log("Map Studio initialized successfully.", "info")

    # ------------------------------------------------------------------
    # Helper Traces & Updates
    # ------------------------------------------------------------------

    def setup_slider_traces(self):
        self.dot_radius_var.trace_add(
            "write", lambda *a: self.dot_radius_label.config(text=f"{self.dot_radius_var.get()} px")
        )
        self.dot_opacity_var.trace_add(
            "write", lambda *a: self.dot_opacity_label.config(text=f"{self.dot_opacity_var.get():.2f}")
        )
        self.heat_radius_var.trace_add(
            "write", lambda *a: self.heat_radius_label.config(text=f"{self.heat_radius_var.get()} px")
        )
        self.heat_blur_var.trace_add(
            "write", lambda *a: self.heat_blur_label.config(text=f"{self.heat_blur_var.get()} px")
        )
        self.heat_min_opacity_var.trace_add(
            "write", lambda *a: self.heat_min_opacity_label.config(text=f"{self.heat_min_opacity_var.get():.2f}")
        )
        self.heat_max_opacity_var.trace_add(
            "write", lambda *a: self.heat_max_opacity_label.config(text=f"{self.heat_max_opacity_var.get():.2f}")
        )

    def refresh_dynamic_sections(self):
        self.dot_frame.pack_forget()
        self.heat_frame.pack_forget()

        mode = self.visualization_var.get()
        if mode in ("Dots", "Dots + Heatmap"):
            self.dot_frame.pack(fill="x", pady=(0, 8))
        if mode in ("Heatmap", "Dots + Heatmap"):
            self.heat_frame.pack(fill="x", pady=4)

    def update_outline_state(self):
        state = "normal" if self.dot_outline_var.get() else "disabled"
        self.outline_spin.configure(state=state)

    def choose_color(self):
        result = colorchooser.askcolor(title="Choose Dot Color", initialcolor=self.selected_color)
        if result and result[1]:
            self.selected_color = result[1]
            self.color_swatch.configure(bg=self.selected_color)
            self.color_hex_label.configure(text=self.selected_color)

    def log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "ℹ️"
        if level == "success":
            prefix = "✓"
        elif level == "warning":
            prefix = "⚠️"
        elif level == "error":
            prefix = "❌"

        log_line = f"[{timestamp}] {prefix} {message}\n"
        if hasattr(self, "log_text"):
            self.log_text.configure(state="normal")
            self.log_text.insert("end", log_line)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Data & Processing Logic
    # ------------------------------------------------------------------

    def browse_csv(self):
        path = filedialog.askopenfilename(
            title="Choose GPS CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.csv_var.set(path)
            self.load_csv()

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Choose Output HTML Map",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=os.path.basename(self.output_var.get()),
        )
        if path:
            self.output_var.set(path)

    def load_csv(self, silent=False):
        path = self.csv_var.get().strip()
        if not path or not os.path.exists(path):
            if not silent:
                messagebox.showerror("File Error", f"CSV path does not exist:\n{path}")
            self.stats_var.set("No CSV file selected or found.")
            return

        try:
            df = pd.read_csv(path)
        except Exception as exc:
            if not silent:
                messagebox.showerror("CSV Error", str(exc))
            self.stats_var.set("Failed to parse CSV file.")
            self.log(f"CSV load error: {exc}", "error")
            return

        if len(df.columns) < 2:
            if not silent:
                messagebox.showerror("CSV Error", "The CSV must contain at least two columns.")
            return

        self.df = df
        columns = [str(c) for c in df.columns]

        self.lat_combo["values"] = columns
        self.lon_combo["values"] = columns

        lower = {str(c).strip().lower(): str(c) for c in df.columns}
        lat_names = ["latitude", "lat", "gps_latitude", "gps_lat", "latitude_deg"]
        lon_names = ["longitude", "lon", "lng", "gps_longitude", "gps_lon", "longitude_deg"]

        lat = next((lower[name] for name in lat_names if name in lower), columns[0])
        lon = next((lower[name] for name in lon_names if name in lower), columns[1])

        self.lat_var.set(lat)
        self.lon_var.set(lon)

        self.stats_var.set(
            f"• Total Dataset Rows: {len(df):,}\n"
            f"• Detected Columns: {len(df.columns)}\n"
            f"• Latitude Column: {lat}\n"
            f"• Longitude Column: {lon}"
        )
        self.log(f"Loaded {len(df):,} rows from '{os.path.basename(path)}'", "success")

    def get_coordinates(self):
        if self.df is None:
            raise ValueError("Please load a valid CSV file first.")

        lat_col = self.lat_var.get()
        lon_col = self.lon_var.get()

        if not lat_col or not lon_col:
            raise ValueError("Please select latitude and longitude columns.")

        work = self.df.copy()
        work[lat_col] = pd.to_numeric(work[lat_col], errors="coerce")
        work[lon_col] = pd.to_numeric(work[lon_col], errors="coerce")
        work = work.dropna(subset=[lat_col, lon_col])

        work = work[work[lat_col].between(-90, 90) & work[lon_col].between(-180, 180)]

        if work.empty:
            raise ValueError("No valid GPS coordinates (-90 to 90, -180 to 180) were found.")

        if self.merge_duplicates_var.get():
            grouped = (
                work.groupby([lat_col, lon_col], as_index=False)
                .size()
                .rename(columns={"size": "_visit_count"})
            )
        else:
            work["_visit_count"] = 1
            grouped = work[[lat_col, lon_col, "_visit_count"]]

        return grouped, lat_col, lon_col

    # ------------------------------------------------------------------
    # Folium Map Generation
    # ------------------------------------------------------------------

    def build_map(self):
        work, lat_col, lon_col = self.get_coordinates()

        avg_lat = work[lat_col].mean()
        avg_lon = work[lon_col].mean()
        provider = MAP_PROVIDERS[self.provider_var.get()]

        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=int(self.zoom_var.get()),
            tiles=provider["tiles"],
            attr=provider["attr"],
            control_scale=True,
            prefer_canvas=True,
        )

        mode = self.visualization_var.get()
        if mode in ("Dots", "Dots + Heatmap"):
            self.add_dots(m, work, lat_col, lon_col)

        if mode in ("Heatmap", "Dots + Heatmap"):
            self.add_heatmap(m, work, lat_col, lon_col)

        if self.fit_bounds_var.get():
            lats = work[lat_col].tolist()
            lons = work[lon_col].tolist()
            if len(lats) == 1:
                m.location = [lats[0], lons[0]]
            else:
                m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(25, 25))

        if self.fullscreen_var.get():
            Fullscreen(
                position="topright",
                title="Full screen",
                title_cancel="Exit full screen",
                force_separate_button=True,
            ).add_to(m)

        if self.mouse_position_var.get():
            MousePosition(
                position="bottomleft",
                separator=" | ",
                prefix="Coordinates:",
                num_digits=5,
            ).add_to(m)

        if self.minimap_var.get():
            MiniMap(toggle_display=True).add_to(m)

        if self.layer_control_var.get():
            folium.LayerControl(collapsed=False).add_to(m)

        return m, len(work)

    def add_dots(self, m, work, lat_col, lon_col):
        if self.cluster_var.get():
            target = MarkerCluster(name="Photo Locations", show=True).add_to(m)
        else:
            target = m

        outline_color = self.selected_color if self.dot_outline_var.get() else None
        outline_weight = int(self.dot_weight_var.get()) if self.dot_outline_var.get() else 0

        for row in work.itertuples(index=False):
            lat = getattr(row, lat_col)
            lon = getattr(row, lon_col)

            folium.CircleMarker(
                location=[lat, lon],
                radius=int(self.dot_radius_var.get()),
                color=outline_color,
                weight=outline_weight,
                fill=True,
                fill_color=self.selected_color,
                fill_opacity=float(self.dot_opacity_var.get()),
            ).add_to(target)

    def add_heatmap(self, m, work, lat_col, lon_col):
        locations = []
        for row in work.itertuples(index=False):
            lat = getattr(row, lat_col)
            lon = getattr(row, lon_col)

            if self.weight_visits_var.get():
                count = max(1, int(getattr(row, "_visit_count")))
                locations.append([lat, lon, count])
            else:
                locations.append([lat, lon])

        HeatMap(
            locations,
            name="Travel Density",
            radius=int(self.heat_radius_var.get()),
            blur=int(self.heat_blur_var.get()),
            min_opacity=float(self.heat_min_opacity_var.get()),
            max_zoom=int(self.heat_max_zoom_var.get()),
            gradient=HEAT_GRADIENTS[self.heat_gradient_var.get()],
        ).add_to(m)

    # ------------------------------------------------------------------
    # Preview & Export Actions
    # ------------------------------------------------------------------

    def update_preview(self):
        try:
            self.root.update_idletasks()
            m, count = self.build_map()

            preview_dir = os.path.join(tempfile.gettempdir(), "photo_gps_map")
            os.makedirs(preview_dir, exist_ok=True)

            preview_path = os.path.join(preview_dir, "preview.html")
            m.save(preview_path)
            self.last_preview_path = preview_path

            webbrowser.open("file://" + preview_path)
            self.log(f"Updated live preview with {count:,} location groups.", "success")

        except Exception as exc:
            self.log(f"Preview failed: {exc}", "error")
            messagebox.showerror("Preview Error", str(exc))

    def open_last_preview(self):
        if not self.last_preview_path or not os.path.exists(self.last_preview_path):
            messagebox.showinfo("No Preview Available", "Please update and generate a preview first.")
            return
        webbrowser.open("file://" + self.last_preview_path)

    def generate_final(self):
        try:
            output = self.output_var.get().strip()
            if not output:
                output = DEFAULT_OUTPUT

            if not output.lower().endswith(".html"):
                output += ".html"

            output = os.path.abspath(os.path.expanduser(output))
            os.makedirs(os.path.dirname(output), exist_ok=True)

            self.root.update_idletasks()
            m, count = self.build_map()
            m.save(output)

            self.log(f"Successfully generated final HTML: {output}", "success")

            if self.open_after_var.get():
                webbrowser.open("file://" + output)

            messagebox.showinfo(
                "Map Exported!",
                f"Your final HTML map has been generated successfully.\n\n"
                f"File: {output}\n"
                f"Coordinate Groups: {count:,}",
            )

        except Exception as exc:
            self.log(f"Final generation failed: {exc}", "error")
            messagebox.showerror("Generation Error", str(exc))


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    root = tk.Tk()
    app = MapStudio(root)
    app.update_outline_state()
    root.mainloop()


if __name__ == "__main__":
    main()