# -*- coding: utf-8 -*-
# Progress Bar Component
# Author: eddy

import customtkinter as ctk
from typing import Callable, Optional

from config import CURRENT_THEME


class ProgressBar(ctk.CTkFrame):
    """Progress bar with time display and seek functionality"""

    def __init__(
        self,
        master,
        on_seek: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._on_seek = on_seek
        self._duration_ms = 0
        self._is_dragging = False

        self._create_widgets()

    def _create_widgets(self):
        """Create progress bar and time labels"""
        theme = CURRENT_THEME

        # Current time label
        self.lbl_current = ctk.CTkLabel(
            self,
            text="00:00",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"],
            width=45
        )
        self.lbl_current.pack(side="left", padx=(0, 5))

        # Progress slider
        self.slider = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            number_of_steps=100,
            height=12,
            progress_color=theme["accent"],
            fg_color=theme["bg_tertiary"],
            button_color=theme["accent"],
            button_hover_color=theme["button_hover"],
            command=self._on_slider_change
        )
        self.slider.set(0)
        self.slider.pack(side="left", fill="x", expand=True, padx=5)

        # Bind mouse events for dragging detection
        self.slider.bind("<Button-1>", self._on_drag_start)
        self.slider.bind("<ButtonRelease-1>", self._on_drag_end)

        # Duration label
        self.lbl_duration = ctk.CTkLabel(
            self,
            text="00:00",
            font=ctk.CTkFont(size=11),
            text_color=theme["text_secondary"],
            width=45
        )
        self.lbl_duration.pack(side="left", padx=(5, 0))

    def _on_slider_change(self, value):
        """Handle slider value change"""
        if self._is_dragging and self._on_seek and self._duration_ms > 0:
            position = value / 100.0
            self._on_seek(position)

    def _on_drag_start(self, event):
        """Handle drag start"""
        self._is_dragging = True

    def _on_drag_end(self, event):
        """Handle drag end"""
        if self._on_seek and self._duration_ms > 0:
            position = self.slider.get() / 100.0
            self._on_seek(position)
        self._is_dragging = False

    def set_position(self, position: float):
        """Set progress position (0.0 to 1.0)"""
        if not self._is_dragging:
            self.slider.set(position * 100)

    def set_current_time(self, time_str: str):
        """Set current time display"""
        self.lbl_current.configure(text=time_str)

    def set_duration(self, duration_str: str, duration_ms: int = 0):
        """Set duration display"""
        self.lbl_duration.configure(text=duration_str)
        self._duration_ms = duration_ms

    def reset(self):
        """Reset progress bar"""
        self.slider.set(0)
        self.lbl_current.configure(text="00:00")
        self.lbl_duration.configure(text="00:00")
        self._duration_ms = 0
