# -*- coding: utf-8 -*-
# API module
# Author: eddy

from .local_scanner import LocalScanner
from .netease_api import NeteaseAPI, OnlineSong
from .lyrics_api import LyricsParser, LyricsManager

__all__ = [
    "LocalScanner",
    "NeteaseAPI",
    "OnlineSong",
    "LyricsParser",
    "LyricsManager"
]
