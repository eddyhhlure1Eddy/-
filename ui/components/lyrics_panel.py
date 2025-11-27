# -*- coding: utf-8 -*-
# Lyrics Display Panel
# Author: eddy

import customtkinter as ctk
from typing import Optional, List, Tuple
import threading

from config import CURRENT_THEME
from api.lyrics_api import LyricsManager, LyricLine
from api.netease_api import NeteaseAPI


class LyricsPanel(ctk.CTkFrame):
    """Lyrics display panel with scrolling animation"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._lyrics_manager = LyricsManager()
        self._api = NeteaseAPI()
        self._current_song_id: Optional[str] = None
        self._lyric_labels: List[ctk.CTkLabel] = []
        self._update_job = None

        self._create_widgets()

    def _create_widgets(self):
        """Create lyrics panel widgets"""
        theme = CURRENT_THEME

        self.configure(fg_color=theme["bg_secondary"], corner_radius=8)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=30)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Lyrics",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme["text_primary"]
        ).pack(side="left")

        # Status indicator
        self.lbl_status = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=theme["text_secondary"]
        )
        self.lbl_status.pack(side="right")

        # Lyrics container (scrollable)
        self.lyrics_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme["bg_tertiary"],
            scrollbar_button_hover_color=theme["accent"]
        )
        self.lyrics_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # No lyrics label
        self.lbl_no_lyrics = ctk.CTkLabel(
            self.lyrics_container,
            text="No lyrics available",
            font=ctk.CTkFont(size=12),
            text_color=theme["text_secondary"]
        )
        self.lbl_no_lyrics.pack(pady=20)

    def load_lyrics(self, song_id: str):
        """Load lyrics for a song"""
        if song_id == self._current_song_id:
            return

        self._current_song_id = song_id
        self._clear_lyrics()
        self.lbl_status.configure(text="Loading...")

        # Load in background
        def load_thread():
            lrc = self._api.get_lyrics(song_id)
            self.after(0, lambda: self._on_lyrics_loaded(lrc))

        threading.Thread(target=load_thread, daemon=True).start()

    def load_lyrics_text(self, lrc_content: str):
        """Load lyrics from LRC text directly"""
        self._clear_lyrics()
        self._lyrics_manager.load(lrc_content)
        self._display_lyrics()

    def _on_lyrics_loaded(self, lrc_content: Optional[str]):
        """Handle loaded lyrics"""
        if lrc_content:
            self._lyrics_manager.load(lrc_content)
            self._display_lyrics()
            self.lbl_status.configure(text="")
        else:
            self.lbl_status.configure(text="Not found")
            self.lbl_no_lyrics.pack(pady=20)

    def _display_lyrics(self):
        """Display lyrics in the container"""
        theme = CURRENT_THEME

        # Hide no lyrics label
        self.lbl_no_lyrics.pack_forget()

        # Create labels for each line
        lines = self._lyrics_manager.get_all_lines()

        for line in lines:
            lbl = ctk.CTkLabel(
                self.lyrics_container,
                text=line.text,
                font=ctk.CTkFont(size=13),
                text_color=theme["text_secondary"],
                wraplength=250
            )
            lbl.pack(pady=3)
            self._lyric_labels.append(lbl)

    def _clear_lyrics(self):
        """Clear current lyrics display"""
        for lbl in self._lyric_labels:
            lbl.destroy()
        self._lyric_labels.clear()
        self._lyrics_manager.clear()
        self.lbl_no_lyrics.pack_forget()

    def update_highlight(self, current_time_ms: int):
        """Update highlighted lyric based on playback time"""
        if not self._lyrics_manager.has_lyrics():
            return

        theme = CURRENT_THEME

        # Get current line index
        lines = self._lyrics_manager.get_all_lines()
        current_idx = 0

        for i, line in enumerate(lines):
            if line.time_ms <= current_time_ms:
                current_idx = i
            else:
                break

        # Update label colors
        for i, lbl in enumerate(self._lyric_labels):
            if i == current_idx:
                lbl.configure(
                    text_color=theme["accent"],
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                # Try to scroll to current line
                try:
                    # Calculate scroll position
                    self.lyrics_container._parent_canvas.yview_moveto(
                        max(0, (current_idx - 3) / max(len(self._lyric_labels), 1))
                    )
                except Exception:
                    pass
            else:
                lbl.configure(
                    text_color=theme["text_secondary"],
                    font=ctk.CTkFont(size=13)
                )

    def clear(self):
        """Clear lyrics and reset"""
        self._current_song_id = None
        self._clear_lyrics()
        self.lbl_status.configure(text="")
        self.lbl_no_lyrics.pack(pady=20)

    def has_lyrics(self) -> bool:
        """Check if lyrics are loaded"""
        return self._lyrics_manager.has_lyrics()


class MiniLyricsDisplay(ctk.CTkFrame):
    """Compact lyrics display for main player view"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._lyrics_manager = LyricsManager()
        self._api = NeteaseAPI()
        self._current_song_id: Optional[str] = None

        self._create_widgets()

    def _create_widgets(self):
        """Create mini lyrics display"""
        theme = CURRENT_THEME

        self.configure(fg_color="transparent")

        # Current line
        self.lbl_current = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=theme["accent"],
            wraplength=350
        )
        self.lbl_current.pack()

        # Next line (dimmed)
        self.lbl_next = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"],
            wraplength=350
        )
        self.lbl_next.pack()

    def load_lyrics(self, song_id: str):
        """Load lyrics for a song"""
        if song_id == self._current_song_id:
            return

        self._current_song_id = song_id
        self._lyrics_manager.clear()
        self.lbl_current.configure(text="Loading lyrics...")
        self.lbl_next.configure(text="")

        # Load in background
        def load_thread():
            lrc = self._api.get_lyrics(song_id)
            self.after(0, lambda: self._on_lyrics_loaded(lrc))

        threading.Thread(target=load_thread, daemon=True).start()

    def _on_lyrics_loaded(self, lrc_content: Optional[str]):
        """Handle loaded lyrics"""
        if lrc_content:
            self._lyrics_manager.load(lrc_content)
            self.lbl_current.configure(text="")
            self.lbl_next.configure(text="")
        else:
            self.lbl_current.configure(text="No lyrics available")
            self.lbl_next.configure(text="")

    def update_display(self, current_time_ms: int):
        """Update lyrics display based on playback time"""
        current, next_line = self._lyrics_manager.get_current_line(current_time_ms)

        if current:
            self.lbl_current.configure(text=current)
        else:
            self.lbl_current.configure(text="")

        if next_line:
            self.lbl_next.configure(text=next_line)
        else:
            self.lbl_next.configure(text="")

    def clear(self):
        """Clear display"""
        self._current_song_id = None
        self._lyrics_manager.clear()
        self.lbl_current.configure(text="")
        self.lbl_next.configure(text="")

    def has_lyrics(self) -> bool:
        """Check if lyrics are loaded"""
        return self._lyrics_manager.has_lyrics()
