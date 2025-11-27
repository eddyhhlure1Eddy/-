# -*- coding: utf-8 -*-
# Playlist Panel Component
# Author: eddy

import customtkinter as ctk
from typing import Callable, Optional, List
from pathlib import Path

from config import CURRENT_THEME
from core.playlist import Song


class PlaylistPanel(ctk.CTkFrame):
    """Playlist display panel with scrollable song list"""

    def __init__(
        self,
        master,
        on_song_select: Optional[Callable[[int], None]] = None,
        on_song_double_click: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self._on_song_select = on_song_select
        self._on_song_double_click = on_song_double_click
        self._songs: List[Song] = []
        self._song_frames: List[ctk.CTkFrame] = []
        self._selected_index = -1

        self._create_widgets()

    def _create_widgets(self):
        """Create playlist panel"""
        theme = CURRENT_THEME

        self.configure(fg_color=theme["bg_secondary"], corner_radius=8)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=35)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Playlist",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme["text_primary"]
        ).pack(side="left")

        self.lbl_count = ctk.CTkLabel(
            header,
            text="0 songs",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"]
        )
        self.lbl_count.pack(side="right")

        # Scrollable frame for songs
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=theme["bg_tertiary"],
            scrollbar_button_hover_color=theme["accent"]
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))

    def set_songs(self, songs: List[Song]):
        """Set playlist songs"""
        self._songs = songs
        self._selected_index = -1
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the song list display"""
        theme = CURRENT_THEME

        # Clear existing frames
        for frame in self._song_frames:
            frame.destroy()
        self._song_frames.clear()

        # Update count
        count = len(self._songs)
        self.lbl_count.configure(text=f"{count} song{'s' if count != 1 else ''}")

        # Create song items
        for i, song in enumerate(self._songs):
            frame = self._create_song_item(i, song)
            self._song_frames.append(frame)

    def _create_song_item(self, index: int, song: Song) -> ctk.CTkFrame:
        """Create a song list item"""
        theme = CURRENT_THEME

        frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="transparent",
            corner_radius=6,
            height=45
        )
        frame.pack(fill="x", pady=2)
        frame.pack_propagate(False)

        # Index number
        ctk.CTkLabel(
            frame,
            text=f"{index + 1:02d}",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"],
            width=30
        ).pack(side="left", padx=(10, 5))

        # Song info container
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        # Title
        title = song.title if len(song.title) < 30 else song.title[:27] + "..."
        ctk.CTkLabel(
            info_frame,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=theme["text_primary"],
            anchor="w"
        ).pack(fill="x", pady=(5, 0))

        # Artist
        ctk.CTkLabel(
            info_frame,
            text=song.artist,
            font=ctk.CTkFont(size=10),
            text_color=theme["text_secondary"],
            anchor="w"
        ).pack(fill="x")

        # Duration
        duration_str = self._format_duration(song.duration)
        ctk.CTkLabel(
            frame,
            text=duration_str,
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"],
            width=45
        ).pack(side="right", padx=10)

        # Bind click events
        frame.bind("<Button-1>", lambda e, idx=index: self._on_click(idx))
        frame.bind("<Double-Button-1>", lambda e, idx=index: self._on_double_click(idx))

        # Make children also clickable
        for child in frame.winfo_children():
            child.bind("<Button-1>", lambda e, idx=index: self._on_click(idx))
            child.bind("<Double-Button-1>", lambda e, idx=index: self._on_double_click(idx))
            if hasattr(child, "winfo_children"):
                for grandchild in child.winfo_children():
                    grandchild.bind("<Button-1>", lambda e, idx=index: self._on_click(idx))
                    grandchild.bind("<Double-Button-1>", lambda e, idx=index: self._on_double_click(idx))

        return frame

    def _on_click(self, index: int):
        """Handle single click on song"""
        self.select_song(index)
        if self._on_song_select:
            self._on_song_select(index)

    def _on_double_click(self, index: int):
        """Handle double click on song"""
        self.select_song(index)
        if self._on_song_double_click:
            self._on_song_double_click(index)

    def select_song(self, index: int):
        """Select a song by index"""
        theme = CURRENT_THEME

        # Deselect previous
        if 0 <= self._selected_index < len(self._song_frames):
            self._song_frames[self._selected_index].configure(
                fg_color="transparent"
            )

        # Select new
        if 0 <= index < len(self._song_frames):
            self._selected_index = index
            self._song_frames[index].configure(
                fg_color=theme["bg_tertiary"]
            )

    def get_selected_index(self) -> int:
        """Get currently selected index"""
        return self._selected_index

    @staticmethod
    def _format_duration(ms: int) -> str:
        """Format milliseconds to MM:SS"""
        if ms <= 0:
            return "--:--"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def clear(self):
        """Clear playlist"""
        self._songs.clear()
        self._selected_index = -1
        self._refresh_list()
