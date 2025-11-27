# -*- coding: utf-8 -*-
# Search Panel Component
# Author: eddy

import customtkinter as ctk
from typing import Callable, Optional, List
import threading

from config import CURRENT_THEME
from api.netease_api import NeteaseAPI, OnlineSong


class SearchPanel(ctk.CTkFrame):
    """Online music search panel"""

    def __init__(
        self,
        master,
        on_song_play: Optional[Callable[[OnlineSong], None]] = None,
        on_song_add: Optional[Callable[[OnlineSong], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self._on_song_play = on_song_play
        self._on_song_add = on_song_add
        self._api = NeteaseAPI()
        self._results: List[OnlineSong] = []
        self._result_frames: List[ctk.CTkFrame] = []
        self._searching = False

        self._create_widgets()

    def _create_widgets(self):
        """Create search panel widgets"""
        theme = CURRENT_THEME

        self.configure(fg_color=theme["bg_secondary"], corner_radius=8)

        # Search input area
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        # Search entry
        self.entry_search = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search songs...",
            height=35,
            corner_radius=17,
            fg_color=theme["bg_tertiary"],
            border_color=theme["bg_tertiary"],
            text_color=theme["text_primary"],
            placeholder_text_color=theme["text_secondary"]
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<Return>", lambda e: self._do_search())

        # Search button
        self.btn_search = ctk.CTkButton(
            search_frame,
            text="Search",
            width=70,
            height=35,
            corner_radius=17,
            fg_color=theme["accent"],
            hover_color=theme["button_hover"],
            command=self._do_search
        )
        self.btn_search.pack(side="right")

        # Mood selection area
        mood_frame = ctk.CTkFrame(self, fg_color="transparent")
        mood_frame.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkLabel(
            mood_frame,
            text="Mood:",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"]
        ).pack(side="left", padx=(0, 5))

        moods = [
            ("Happy", "happy"),
            ("Sad", "sad"),
            ("Relax", "relaxed"),
            ("Energy", "energetic"),
            ("Love", "romantic"),
            ("Focus", "focus"),
        ]

        for label, mood in moods:
            btn = ctk.CTkButton(
                mood_frame,
                text=label,
                width=50,
                height=25,
                corner_radius=12,
                fg_color=theme["bg_tertiary"],
                hover_color=theme["accent"],
                font=ctk.CTkFont(size=10),
                command=lambda m=mood: self._load_mood_playlist(m)
            )
            btn.pack(side="left", padx=2)

        # Status label
        self.lbl_status = ctk.CTkLabel(
            self,
            text="Enter keywords or select a mood",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"]
        )
        self.lbl_status.pack(pady=(0, 5))

        # Results scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme["bg_tertiary"],
            scrollbar_button_hover_color=theme["accent"]
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))

    def _do_search(self):
        """Execute search"""
        keyword = self.entry_search.get().strip()
        if not keyword or self._searching:
            return

        self._searching = True
        self.lbl_status.configure(text="Searching...")
        self.btn_search.configure(state="disabled")

        # Clear previous results
        self._clear_results()

        # Search in background thread
        def search_thread():
            results = self._api.search(keyword, limit=20)
            self.after(0, lambda: self._show_results(results))

        threading.Thread(target=search_thread, daemon=True).start()

    def _show_results(self, results: List[OnlineSong]):
        """Display search results"""
        self._searching = False
        self.btn_search.configure(state="normal")
        self._results = results

        if not results:
            self.lbl_status.configure(text="No results found")
            return

        self.lbl_status.configure(text=f"Found {len(results)} songs")

        # Create result items
        for i, song in enumerate(results):
            frame = self._create_result_item(i, song)
            self._result_frames.append(frame)

    def _create_result_item(self, index: int, song: OnlineSong) -> ctk.CTkFrame:
        """Create a search result item"""
        theme = CURRENT_THEME

        frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="transparent",
            corner_radius=6,
            height=50
        )
        frame.pack(fill="x", pady=2)
        frame.pack_propagate(False)

        # Song info
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10)

        # Title
        title = song.name if len(song.name) < 25 else song.name[:22] + "..."
        ctk.CTkLabel(
            info_frame,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=theme["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(8, 0))

        # Artist - Album
        info_text = song.artist
        if song.album:
            info_text += f" - {song.album}"
        if len(info_text) > 35:
            info_text = info_text[:32] + "..."

        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            text_color=theme["text_secondary"],
            anchor="w"
        ).pack(fill="x")

        # Duration
        duration_str = self._format_duration(song.duration)
        ctk.CTkLabel(
            frame,
            text=duration_str,
            font=ctk.CTkFont(size=10),
            text_color=theme["text_secondary"],
            width=40
        ).pack(side="left", padx=5)

        # Play button
        btn_play = ctk.CTkButton(
            frame,
            text="\u25B6",
            width=30,
            height=30,
            corner_radius=15,
            fg_color=theme["accent"],
            hover_color=theme["button_hover"],
            font=ctk.CTkFont(size=12),
            command=lambda s=song: self._on_play_click(s)
        )
        btn_play.pack(side="right", padx=(5, 10))

        # Add button
        btn_add = ctk.CTkButton(
            frame,
            text="+",
            width=30,
            height=30,
            corner_radius=15,
            fg_color=theme["bg_tertiary"],
            hover_color=theme["button_hover"],
            font=ctk.CTkFont(size=14),
            command=lambda s=song: self._on_add_click(s)
        )
        btn_add.pack(side="right", padx=5)

        # Hover effect
        def on_enter(e):
            frame.configure(fg_color=theme["bg_tertiary"])

        def on_leave(e):
            frame.configure(fg_color="transparent")

        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)

        return frame

    def _on_play_click(self, song: OnlineSong):
        """Handle play button click"""
        if self._on_song_play:
            # Get play URL if not present
            if not song.play_url:
                def get_url_thread():
                    url = self._api.get_play_url(song.id)
                    if url:
                        song.play_url = url
                        self.after(0, lambda: self._on_song_play(song))

                threading.Thread(target=get_url_thread, daemon=True).start()
            else:
                self._on_song_play(song)

    def _on_add_click(self, song: OnlineSong):
        """Handle add button click"""
        if self._on_song_add:
            # Get play URL if not present
            if not song.play_url:
                def get_url_thread():
                    url = self._api.get_play_url(song.id)
                    if url:
                        song.play_url = url
                        self.after(0, lambda: self._on_song_add(song))

                threading.Thread(target=get_url_thread, daemon=True).start()
            else:
                self._on_song_add(song)

    def _clear_results(self):
        """Clear search results"""
        for frame in self._result_frames:
            frame.destroy()
        self._result_frames.clear()
        self._results.clear()

    @staticmethod
    def _format_duration(ms: int) -> str:
        """Format milliseconds to MM:SS"""
        if ms <= 0:
            return "--:--"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _load_mood_playlist(self, mood: str):
        """Load playlist based on mood"""
        if self._searching:
            return

        self._searching = True
        mood_names = {
            "happy": "Happy",
            "sad": "Sad",
            "relaxed": "Relaxed",
            "energetic": "Energetic",
            "romantic": "Romantic",
            "focus": "Focus"
        }
        self.lbl_status.configure(text=f"Loading {mood_names.get(mood, mood)} playlist...")

        self._clear_results()

        def mood_thread():
            results = self._api.get_mood_playlist(mood, limit=30)
            self.after(0, lambda: self._show_results(results))

        threading.Thread(target=mood_thread, daemon=True).start()

    def focus_search(self):
        """Focus on search entry"""
        self.entry_search.focus_set()
