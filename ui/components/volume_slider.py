# -*- coding: utf-8 -*-
# Volume Slider Component
# Author: eddy

import customtkinter as ctk
from typing import Callable, Optional

from config import CURRENT_THEME, DEFAULT_VOLUME


class VolumeSlider(ctk.CTkFrame):
    """Volume control with icon and slider"""

    VOLUME_HIGH = "\U0001F50A"    # Speaker high
    VOLUME_LOW = "\U0001F509"     # Speaker medium
    VOLUME_MUTE = "\U0001F507"    # Speaker muted

    def __init__(
        self,
        master,
        on_volume_change: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._on_volume_change = on_volume_change
        self._volume = DEFAULT_VOLUME
        self._muted = False
        self._pre_mute_volume = DEFAULT_VOLUME

        self._create_widgets()

    def _create_widgets(self):
        """Create volume icon and slider"""
        theme = CURRENT_THEME

        # Volume icon button (click to mute)
        self.btn_volume = ctk.CTkButton(
            self,
            text=self.VOLUME_HIGH,
            width=30,
            height=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color=theme["button_hover"],
            text_color=theme["text_secondary"],
            font=ctk.CTkFont(size=14),
            command=self._toggle_mute
        )
        self.btn_volume.pack(side="left", padx=(0, 5))

        # Volume slider
        self.slider = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            number_of_steps=100,
            width=100,
            height=12,
            progress_color=theme["accent"],
            fg_color=theme["bg_tertiary"],
            button_color=theme["text_secondary"],
            button_hover_color=theme["text_primary"],
            command=self._on_slider_change
        )
        self.slider.set(self._volume)
        self.slider.pack(side="left", fill="x", expand=True)

    def _on_slider_change(self, value):
        """Handle slider value change"""
        self._volume = int(value)
        self._muted = False
        self._update_icon()

        if self._on_volume_change:
            self._on_volume_change(self._volume)

    def _toggle_mute(self):
        """Toggle mute state"""
        if self._muted:
            # Unmute
            self._muted = False
            self._volume = self._pre_mute_volume
            self.slider.set(self._volume)
        else:
            # Mute
            self._pre_mute_volume = self._volume
            self._muted = True
            self._volume = 0
            self.slider.set(0)

        self._update_icon()

        if self._on_volume_change:
            self._on_volume_change(self._volume)

    def _update_icon(self):
        """Update volume icon based on level"""
        if self._muted or self._volume == 0:
            self.btn_volume.configure(text=self.VOLUME_MUTE)
        elif self._volume < 50:
            self.btn_volume.configure(text=self.VOLUME_LOW)
        else:
            self.btn_volume.configure(text=self.VOLUME_HIGH)

    def get_volume(self) -> int:
        """Get current volume"""
        return self._volume

    def set_volume(self, volume: int):
        """Set volume level"""
        self._volume = max(0, min(100, volume))
        self._muted = self._volume == 0
        self.slider.set(self._volume)
        self._update_icon()

    def is_muted(self) -> bool:
        """Check if muted"""
        return self._muted
