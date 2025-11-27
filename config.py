# -*- coding: utf-8 -*-
# Mini Music Player Configuration
# Author: eddy

import os
from pathlib import Path

# Application Info
APP_NAME = "Mini Music Player"
APP_VERSION = "1.0.0"
AUTHOR = "eddy"

# Window Settings
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 320
MINI_WIDTH = 320
MINI_HEIGHT = 80

# Paths
APP_DIR = Path(__file__).parent
RESOURCES_DIR = APP_DIR / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
THEMES_DIR = RESOURCES_DIR / "themes"
CACHE_DIR = APP_DIR / "cache"

# Audio Settings
SUPPORTED_FORMATS = [".mp3", ".flac", ".wav", ".ogg", ".m4a", ".wma", ".aac"]
DEFAULT_VOLUME = 70

# UI Theme
DARK_THEME = {
    "bg_primary": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_tertiary": "#0f3460",
    "accent": "#e94560",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0a0",
    "button_hover": "#533483",
}

LIGHT_THEME = {
    "bg_primary": "#f5f5f5",
    "bg_secondary": "#ffffff",
    "bg_tertiary": "#e0e0e0",
    "accent": "#e94560",
    "text_primary": "#1a1a2e",
    "text_secondary": "#666666",
    "button_hover": "#d0d0d0",
}

# Default theme
CURRENT_THEME = DARK_THEME

# Play modes
PLAY_MODE_SEQUENCE = 0
PLAY_MODE_LOOP_ONE = 1
PLAY_MODE_LOOP_ALL = 2
PLAY_MODE_SHUFFLE = 3

# Create cache directory if not exists
CACHE_DIR.mkdir(exist_ok=True)
