# -*- coding: utf-8 -*-
# Player Control Buttons
# Author: eddy

import customtkinter as ctk
from typing import Callable, Optional

from config import (
    CURRENT_THEME,
    PLAY_MODE_SEQUENCE,
    PLAY_MODE_LOOP_ONE,
    PLAY_MODE_LOOP_ALL,
    PLAY_MODE_SHUFFLE
)


class PlayerControls(ctk.CTkFrame):
    """Player control buttons: prev, play/pause, next, shuffle, repeat"""

    PLAY_SYMBOL = "\u25B6"      # Play triangle
    PAUSE_SYMBOL = "\u23F8"     # Pause symbol
    PREV_SYMBOL = "\u23EE"      # Previous track
    NEXT_SYMBOL = "\u23ED"      # Next track
    SHUFFLE_SYMBOL = "\U0001F500"  # Shuffle
    REPEAT_SYMBOL = "\U0001F501"   # Repeat
    REPEAT_ONE_SYMBOL = "\U0001F502"  # Repeat one

    def __init__(
        self,
        master,
        on_prev: Optional[Callable] = None,
        on_play_pause: Optional[Callable] = None,
        on_next: Optional[Callable] = None,
        on_mode_change: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._on_prev = on_prev
        self._on_play_pause = on_play_pause
        self._on_next = on_next
        self._on_mode_change = on_mode_change

        self._is_playing = False
        self._play_mode = PLAY_MODE_SEQUENCE

        self._create_widgets()

    def _create_widgets(self):
        """Create control buttons"""
        theme = CURRENT_THEME
        btn_size = 40
        small_btn_size = 35

        # Previous button
        self.btn_prev = ctk.CTkButton(
            self,
            text=self.PREV_SYMBOL,
            width=btn_size,
            height=btn_size,
            corner_radius=btn_size // 2,
            fg_color=theme["bg_tertiary"],
            hover_color=theme["button_hover"],
            text_color=theme["text_primary"],
            font=ctk.CTkFont(size=16),
            command=self._handle_prev
        )
        self.btn_prev.pack(side="left", padx=5)

        # Play/Pause button (larger)
        self.btn_play = ctk.CTkButton(
            self,
            text=self.PLAY_SYMBOL,
            width=50,
            height=50,
            corner_radius=25,
            fg_color=theme["accent"],
            hover_color=theme["button_hover"],
            text_color=theme["text_primary"],
            font=ctk.CTkFont(size=20),
            command=self._handle_play_pause
        )
        self.btn_play.pack(side="left", padx=10)

        # Next button
        self.btn_next = ctk.CTkButton(
            self,
            text=self.NEXT_SYMBOL,
            width=btn_size,
            height=btn_size,
            corner_radius=btn_size // 2,
            fg_color=theme["bg_tertiary"],
            hover_color=theme["button_hover"],
            text_color=theme["text_primary"],
            font=ctk.CTkFont(size=16),
            command=self._handle_next
        )
        self.btn_next.pack(side="left", padx=5)

        # Spacer
        ctk.CTkLabel(self, text="", width=20).pack(side="left")

        # Shuffle button
        self.btn_shuffle = ctk.CTkButton(
            self,
            text=self.SHUFFLE_SYMBOL,
            width=small_btn_size,
            height=small_btn_size,
            corner_radius=small_btn_size // 2,
            fg_color="transparent",
            hover_color=theme["button_hover"],
            text_color=theme["text_secondary"],
            font=ctk.CTkFont(size=14),
            command=self._handle_shuffle
        )
        self.btn_shuffle.pack(side="left", padx=3)

        # Repeat button
        self.btn_repeat = ctk.CTkButton(
            self,
            text=self.REPEAT_SYMBOL,
            width=small_btn_size,
            height=small_btn_size,
            corner_radius=small_btn_size // 2,
            fg_color="transparent",
            hover_color=theme["button_hover"],
            text_color=theme["text_secondary"],
            font=ctk.CTkFont(size=14),
            command=self._handle_repeat
        )
        self.btn_repeat.pack(side="left", padx=3)

    def _handle_prev(self):
        if self._on_prev:
            self._on_prev()

    def _handle_play_pause(self):
        if self._on_play_pause:
            self._on_play_pause()

    def _handle_next(self):
        if self._on_next:
            self._on_next()

    def _handle_shuffle(self):
        """Toggle shuffle mode"""
        if self._play_mode == PLAY_MODE_SHUFFLE:
            self._play_mode = PLAY_MODE_SEQUENCE
        else:
            self._play_mode = PLAY_MODE_SHUFFLE
        self._update_mode_buttons()
        if self._on_mode_change:
            self._on_mode_change(self._play_mode)

    def _handle_repeat(self):
        """Cycle through repeat modes"""
        if self._play_mode == PLAY_MODE_SHUFFLE:
            return  # Don't change repeat if shuffle is on

        if self._play_mode == PLAY_MODE_SEQUENCE:
            self._play_mode = PLAY_MODE_LOOP_ALL
        elif self._play_mode == PLAY_MODE_LOOP_ALL:
            self._play_mode = PLAY_MODE_LOOP_ONE
        else:
            self._play_mode = PLAY_MODE_SEQUENCE

        self._update_mode_buttons()
        if self._on_mode_change:
            self._on_mode_change(self._play_mode)

    def _update_mode_buttons(self):
        """Update button appearance based on mode"""
        theme = CURRENT_THEME

        # Shuffle button
        if self._play_mode == PLAY_MODE_SHUFFLE:
            self.btn_shuffle.configure(
                text_color=theme["accent"],
                fg_color=theme["bg_tertiary"]
            )
        else:
            self.btn_shuffle.configure(
                text_color=theme["text_secondary"],
                fg_color="transparent"
            )

        # Repeat button
        if self._play_mode == PLAY_MODE_LOOP_ONE:
            self.btn_repeat.configure(
                text=self.REPEAT_ONE_SYMBOL,
                text_color=theme["accent"],
                fg_color=theme["bg_tertiary"]
            )
        elif self._play_mode == PLAY_MODE_LOOP_ALL:
            self.btn_repeat.configure(
                text=self.REPEAT_SYMBOL,
                text_color=theme["accent"],
                fg_color=theme["bg_tertiary"]
            )
        else:
            self.btn_repeat.configure(
                text=self.REPEAT_SYMBOL,
                text_color=theme["text_secondary"],
                fg_color="transparent"
            )

    def set_playing(self, is_playing: bool):
        """Update play/pause button state"""
        self._is_playing = is_playing
        self.btn_play.configure(
            text=self.PAUSE_SYMBOL if is_playing else self.PLAY_SYMBOL
        )

    def set_play_mode(self, mode: int):
        """Set current play mode"""
        self._play_mode = mode
        self._update_mode_buttons()

    def get_play_mode(self) -> int:
        """Get current play mode"""
        return self._play_mode
