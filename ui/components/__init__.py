# -*- coding: utf-8 -*-
# UI Components
# Author: eddy

from .player_controls import PlayerControls
from .progress_bar import ProgressBar
from .volume_slider import VolumeSlider
from .song_info import SongInfo
from .playlist_panel import PlaylistPanel
from .search_panel import SearchPanel
from .lyrics_panel import LyricsPanel, MiniLyricsDisplay
from .settings_panel import SettingsPanel, SettingsManager

__all__ = [
    "PlayerControls",
    "ProgressBar",
    "VolumeSlider",
    "SongInfo",
    "PlaylistPanel",
    "SearchPanel",
    "LyricsPanel",
    "MiniLyricsDisplay",
    "SettingsPanel",
    "SettingsManager"
]
