# -*- coding: utf-8 -*-
# Settings Panel
# Author: eddy

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
import json
from pathlib import Path

from config import CURRENT_THEME, DARK_THEME, LIGHT_THEME, APP_DIR


class SettingsManager:
    """Manage application settings"""

    SETTINGS_FILE = "settings.json"
    DEFAULT_SETTINGS = {
        "theme": "dark",
        "volume": 70,
        "play_mode": 0,
        "auto_play": False,
        "show_lyrics": True,
        "cache_enabled": True,
        "max_cache_mb": 500,
    }

    def __init__(self):
        self._settings_path = APP_DIR / self.SETTINGS_FILE
        self._settings = self.DEFAULT_SETTINGS.copy()
        self._load()

    def _load(self):
        """Load settings from file"""
        if self._settings_path.exists():
            try:
                with open(self._settings_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._settings.update(loaded)
            except Exception:
                pass

    def save(self):
        """Save settings to file"""
        try:
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value"""
        self._settings[key] = value
        self.save()

    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self._settings.copy()


class SettingsPanel(ctk.CTkToplevel):
    """Settings dialog window"""

    def __init__(
        self,
        master,
        settings_manager: SettingsManager,
        on_theme_change: Optional[Callable[[str], None]] = None,
        on_cache_clear: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self._settings = settings_manager
        self._on_theme_change = on_theme_change
        self._on_cache_clear = on_cache_clear

        # Window setup
        self.title("Settings")
        self.geometry("350x400")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - 350) // 2
        y = master.winfo_y() + (master.winfo_height() - 400) // 2
        self.geometry(f"+{x}+{y}")

        self._create_widgets()

    def _create_widgets(self):
        """Create settings widgets"""
        theme = CURRENT_THEME

        self.configure(fg_color=theme["bg_primary"])

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        ctk.CTkLabel(
            main_frame,
            text="Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=theme["text_primary"]
        ).pack(pady=(0, 20))

        # --- Appearance Section ---
        self._create_section_header(main_frame, "Appearance")

        # Theme selector
        theme_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            theme_frame,
            text="Theme",
            font=ctk.CTkFont(size=12),
            text_color=theme["text_primary"]
        ).pack(side="left")

        self.theme_var = ctk.StringVar(value=self._settings.get("theme", "dark"))
        self.theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["dark", "light"],
            variable=self.theme_var,
            width=120,
            height=28,
            fg_color=theme["bg_tertiary"],
            button_color=theme["bg_tertiary"],
            button_hover_color=theme["button_hover"],
            dropdown_fg_color=theme["bg_secondary"],
            dropdown_hover_color=theme["button_hover"],
            command=self._on_theme_select
        )
        self.theme_menu.pack(side="right")

        # --- Playback Section ---
        self._create_section_header(main_frame, "Playback")

        # Show lyrics
        lyrics_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        lyrics_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            lyrics_frame,
            text="Show Lyrics",
            font=ctk.CTkFont(size=12),
            text_color=theme["text_primary"]
        ).pack(side="left")

        self.lyrics_var = ctk.BooleanVar(value=self._settings.get("show_lyrics", True))
        self.lyrics_switch = ctk.CTkSwitch(
            lyrics_frame,
            text="",
            variable=self.lyrics_var,
            onvalue=True,
            offvalue=False,
            progress_color=theme["accent"],
            command=lambda: self._settings.set("show_lyrics", self.lyrics_var.get())
        )
        self.lyrics_switch.pack(side="right")

        # Auto play
        auto_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        auto_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            auto_frame,
            text="Auto Play Next",
            font=ctk.CTkFont(size=12),
            text_color=theme["text_primary"]
        ).pack(side="left")

        self.auto_var = ctk.BooleanVar(value=self._settings.get("auto_play", True))
        self.auto_switch = ctk.CTkSwitch(
            auto_frame,
            text="",
            variable=self.auto_var,
            onvalue=True,
            offvalue=False,
            progress_color=theme["accent"],
            command=lambda: self._settings.set("auto_play", self.auto_var.get())
        )
        self.auto_switch.pack(side="right")

        # --- Cache Section ---
        self._create_section_header(main_frame, "Cache")

        # Enable cache
        cache_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        cache_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            cache_frame,
            text="Enable Cache",
            font=ctk.CTkFont(size=12),
            text_color=theme["text_primary"]
        ).pack(side="left")

        self.cache_var = ctk.BooleanVar(value=self._settings.get("cache_enabled", True))
        self.cache_switch = ctk.CTkSwitch(
            cache_frame,
            text="",
            variable=self.cache_var,
            onvalue=True,
            offvalue=False,
            progress_color=theme["accent"],
            command=lambda: self._settings.set("cache_enabled", self.cache_var.get())
        )
        self.cache_switch.pack(side="right")

        # Clear cache button
        self.btn_clear_cache = ctk.CTkButton(
            main_frame,
            text="Clear Cache",
            width=120,
            height=32,
            corner_radius=16,
            fg_color=theme["bg_tertiary"],
            hover_color=theme["button_hover"],
            command=self._clear_cache
        )
        self.btn_clear_cache.pack(pady=15)

        # --- About Section ---
        self._create_section_header(main_frame, "About")

        ctk.CTkLabel(
            main_frame,
            text="Mini Music Player v1.0.0",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"]
        ).pack()

        ctk.CTkLabel(
            main_frame,
            text="Created by eddy",
            font=ctk.CTkFont(size=10),
            text_color=theme["text_secondary"]
        ).pack()

    def _create_section_header(self, parent, text: str):
        """Create a section header"""
        theme = CURRENT_THEME

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(15, 5))

        ctk.CTkLabel(
            frame,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme["accent"]
        ).pack(side="left")

        # Separator line
        sep = ctk.CTkFrame(
            frame,
            height=1,
            fg_color=theme["bg_tertiary"]
        )
        sep.pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _on_theme_select(self, value: str):
        """Handle theme selection"""
        self._settings.set("theme", value)
        if self._on_theme_change:
            self._on_theme_change(value)

    def _clear_cache(self):
        """Handle clear cache button"""
        if self._on_cache_clear:
            self._on_cache_clear()
        self.btn_clear_cache.configure(text="Cleared!")
        self.after(2000, lambda: self.btn_clear_cache.configure(text="Clear Cache"))
