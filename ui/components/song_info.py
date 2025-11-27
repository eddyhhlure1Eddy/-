# -*- coding: utf-8 -*-
# Song Info Display Component
# Author: eddy

import customtkinter as ctk
from typing import Optional
from pathlib import Path
import io

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from config import CURRENT_THEME, RESOURCES_DIR


class SongInfo(ctk.CTkFrame):
    """Display song information with cover art"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._cover_size = (80, 80)
        self._default_cover = None

        self._create_widgets()
        self._load_default_cover()

    def _create_widgets(self):
        """Create song info display"""
        theme = CURRENT_THEME

        # Cover art frame
        self.cover_frame = ctk.CTkFrame(
            self,
            width=self._cover_size[0],
            height=self._cover_size[1],
            corner_radius=8,
            fg_color=theme["bg_tertiary"]
        )
        self.cover_frame.pack(side="left", padx=(0, 15))
        self.cover_frame.pack_propagate(False)

        # Cover image label
        self.lbl_cover = ctk.CTkLabel(
            self.cover_frame,
            text="\U0001F3B5",  # Music note emoji
            font=ctk.CTkFont(size=32),
            text_color=theme["text_secondary"]
        )
        self.lbl_cover.place(relx=0.5, rely=0.5, anchor="center")

        # Info container
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        # Song title
        self.lbl_title = ctk.CTkLabel(
            info_frame,
            text="No song playing",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=theme["text_primary"],
            anchor="w"
        )
        self.lbl_title.pack(fill="x", pady=(5, 2))

        # Artist name
        self.lbl_artist = ctk.CTkLabel(
            info_frame,
            text="Select a song to play",
            font=ctk.CTkFont(size=12),
            text_color=theme["text_secondary"],
            anchor="w"
        )
        self.lbl_artist.pack(fill="x", pady=(0, 2))

        # Album name
        self.lbl_album = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"],
            anchor="w"
        )
        self.lbl_album.pack(fill="x")

    def _load_default_cover(self):
        """Load default cover image"""
        if not PIL_AVAILABLE:
            return

        # Try to load from resources
        default_path = RESOURCES_DIR / "default_cover.png"
        if default_path.exists():
            try:
                img = Image.open(default_path)
                img.thumbnail(self._cover_size, Image.Resampling.LANCZOS)
                self._default_cover = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=self._cover_size
                )
            except Exception:
                pass

    def update_info(
        self,
        title: str = "",
        artist: str = "",
        album: str = "",
        cover_data: Optional[bytes] = None
    ):
        """Update song information display"""
        # Update text
        self.lbl_title.configure(text=title if title else "No song playing")
        self.lbl_artist.configure(text=artist if artist else "Unknown Artist")
        self.lbl_album.configure(text=album if album else "")

        # Update cover
        self._update_cover(cover_data)

    def _update_cover(self, cover_data: Optional[bytes]):
        """Update cover art"""
        if not PIL_AVAILABLE:
            return

        if cover_data:
            try:
                img = Image.open(io.BytesIO(cover_data))
                img.thumbnail(self._cover_size, Image.Resampling.LANCZOS)
                ctk_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=self._cover_size
                )
                self.lbl_cover.configure(image=ctk_image, text="")
                self.lbl_cover._image = ctk_image  # Keep reference
                return
            except Exception:
                pass

        # Use default or emoji
        if self._default_cover:
            self.lbl_cover.configure(image=self._default_cover, text="")
        else:
            self.lbl_cover.configure(image=None, text="\U0001F3B5")

    def clear(self):
        """Clear song info"""
        self.update_info()
