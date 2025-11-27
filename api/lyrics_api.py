# -*- coding: utf-8 -*-
# Lyrics Parser and Manager
# Author: eddy

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LyricLine:
    """Single lyric line with timestamp"""
    time_ms: int  # Time in milliseconds
    text: str


class LyricsParser:
    """Parse and manage LRC format lyrics"""

    # LRC timestamp pattern: [mm:ss.xx] or [mm:ss:xx] or [mm:ss]
    TIME_PATTERN = re.compile(r'\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\]')

    @staticmethod
    def parse(lrc_content: str) -> List[LyricLine]:
        """
        Parse LRC format lyrics

        Args:
            lrc_content: LRC format string

        Returns:
            List of LyricLine sorted by time
        """
        lines = []

        if not lrc_content:
            return lines

        for line in lrc_content.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Find all timestamps in the line
            timestamps = []
            text = line

            for match in LyricsParser.TIME_PATTERN.finditer(line):
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                ms_str = match.group(3)

                # Handle different millisecond formats
                if ms_str:
                    if len(ms_str) == 2:
                        milliseconds = int(ms_str) * 10
                    elif len(ms_str) == 3:
                        milliseconds = int(ms_str)
                    else:
                        milliseconds = int(ms_str[:3])
                else:
                    milliseconds = 0

                time_ms = (minutes * 60 + seconds) * 1000 + milliseconds
                timestamps.append(time_ms)

                # Remove timestamp from text
                text = text.replace(match.group(0), '', 1)

            # Clean up text
            text = text.strip()

            # Skip metadata lines
            if text.startswith('[') and ':' in text:
                continue

            # Create lyric lines for each timestamp
            for time_ms in timestamps:
                if text:  # Only add non-empty lines
                    lines.append(LyricLine(time_ms=time_ms, text=text))

        # Sort by time
        lines.sort(key=lambda x: x.time_ms)

        return lines

    @staticmethod
    def format_time(ms: int) -> str:
        """Format milliseconds to MM:SS"""
        if ms < 0:
            return "00:00"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


class LyricsManager:
    """Manage lyrics playback"""

    def __init__(self):
        self._lyrics: List[LyricLine] = []
        self._current_index = 0

    def load(self, lrc_content: str):
        """Load lyrics from LRC content"""
        self._lyrics = LyricsParser.parse(lrc_content)
        self._current_index = 0

    def clear(self):
        """Clear lyrics"""
        self._lyrics.clear()
        self._current_index = 0

    def get_current_line(self, current_time_ms: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Get current and next lyric lines based on playback time

        Args:
            current_time_ms: Current playback time in milliseconds

        Returns:
            Tuple of (current_line, next_line)
        """
        if not self._lyrics:
            return None, None

        current_line = None
        next_line = None

        # Find current lyric line
        for i, lyric in enumerate(self._lyrics):
            if lyric.time_ms <= current_time_ms:
                current_line = lyric.text
                self._current_index = i
            else:
                next_line = lyric.text
                break

        return current_line, next_line

    def get_line_at_index(self, index: int) -> Optional[LyricLine]:
        """Get lyric line at specific index"""
        if 0 <= index < len(self._lyrics):
            return self._lyrics[index]
        return None

    def get_all_lines(self) -> List[LyricLine]:
        """Get all lyric lines"""
        return self._lyrics.copy()

    def get_current_index(self) -> int:
        """Get current line index"""
        return self._current_index

    def get_lines_around(self, current_time_ms: int, before: int = 2, after: int = 2) -> List[Tuple[LyricLine, bool]]:
        """
        Get lyric lines around current time

        Args:
            current_time_ms: Current playback time
            before: Number of lines before current
            after: Number of lines after current

        Returns:
            List of (LyricLine, is_current) tuples
        """
        if not self._lyrics:
            return []

        # Find current index
        current_idx = 0
        for i, lyric in enumerate(self._lyrics):
            if lyric.time_ms <= current_time_ms:
                current_idx = i
            else:
                break

        # Get range
        start = max(0, current_idx - before)
        end = min(len(self._lyrics), current_idx + after + 1)

        result = []
        for i in range(start, end):
            is_current = (i == current_idx)
            result.append((self._lyrics[i], is_current))

        return result

    def has_lyrics(self) -> bool:
        """Check if lyrics are loaded"""
        return len(self._lyrics) > 0

    def __len__(self) -> int:
        return len(self._lyrics)
