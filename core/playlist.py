# -*- coding: utf-8 -*-
# Playlist Management
# Author: eddy

import random
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

from config import PLAY_MODE_SEQUENCE, PLAY_MODE_LOOP_ONE, PLAY_MODE_LOOP_ALL, PLAY_MODE_SHUFFLE


@dataclass
class Song:
    """Represents a song in the playlist"""
    path: str
    title: str = ""
    artist: str = "Unknown Artist"
    album: str = "Unknown Album"
    duration: int = 0  # milliseconds
    cover_path: Optional[str] = None

    def __post_init__(self):
        if not self.title:
            self.title = Path(self.path).stem


@dataclass
class Playlist:
    """Manages a list of songs with playback control"""
    name: str = "Default Playlist"
    songs: List[Song] = field(default_factory=list)
    _current_index: int = -1
    _play_mode: int = PLAY_MODE_SEQUENCE
    _shuffle_indices: List[int] = field(default_factory=list)
    _shuffle_position: int = 0

    def add_song(self, song: Song):
        """Add a song to the playlist"""
        self.songs.append(song)
        self._update_shuffle_indices()

    def add_songs(self, songs: List[Song]):
        """Add multiple songs to the playlist"""
        self.songs.extend(songs)
        self._update_shuffle_indices()

    def remove_song(self, index: int) -> bool:
        """Remove a song by index"""
        if 0 <= index < len(self.songs):
            self.songs.pop(index)
            if self._current_index >= len(self.songs):
                self._current_index = len(self.songs) - 1
            self._update_shuffle_indices()
            return True
        return False

    def clear(self):
        """Clear all songs"""
        self.songs.clear()
        self._current_index = -1
        self._shuffle_indices.clear()

    def get_current_song(self) -> Optional[Song]:
        """Get the currently selected song"""
        if 0 <= self._current_index < len(self.songs):
            return self.songs[self._current_index]
        return None

    def get_current_index(self) -> int:
        """Get current song index"""
        return self._current_index

    def set_current_index(self, index: int) -> bool:
        """Set current song by index"""
        if 0 <= index < len(self.songs):
            self._current_index = index
            return True
        return False

    def next_song(self) -> Optional[Song]:
        """Move to next song based on play mode"""
        if not self.songs:
            return None

        if self._play_mode == PLAY_MODE_LOOP_ONE:
            # Stay on current song
            pass
        elif self._play_mode == PLAY_MODE_SHUFFLE:
            self._shuffle_position += 1
            if self._shuffle_position >= len(self._shuffle_indices):
                self._shuffle_position = 0
                self._update_shuffle_indices()
            self._current_index = self._shuffle_indices[self._shuffle_position]
        else:
            # Sequence or Loop All
            self._current_index += 1
            if self._current_index >= len(self.songs):
                if self._play_mode == PLAY_MODE_LOOP_ALL:
                    self._current_index = 0
                else:
                    self._current_index = len(self.songs) - 1
                    return None  # End of playlist in sequence mode

        return self.get_current_song()

    def previous_song(self) -> Optional[Song]:
        """Move to previous song"""
        if not self.songs:
            return None

        if self._play_mode == PLAY_MODE_SHUFFLE:
            self._shuffle_position -= 1
            if self._shuffle_position < 0:
                self._shuffle_position = len(self._shuffle_indices) - 1
            self._current_index = self._shuffle_indices[self._shuffle_position]
        else:
            self._current_index -= 1
            if self._current_index < 0:
                if self._play_mode == PLAY_MODE_LOOP_ALL:
                    self._current_index = len(self.songs) - 1
                else:
                    self._current_index = 0

        return self.get_current_song()

    def get_play_mode(self) -> int:
        """Get current play mode"""
        return self._play_mode

    def set_play_mode(self, mode: int):
        """Set play mode"""
        if mode in [PLAY_MODE_SEQUENCE, PLAY_MODE_LOOP_ONE, PLAY_MODE_LOOP_ALL, PLAY_MODE_SHUFFLE]:
            self._play_mode = mode
            if mode == PLAY_MODE_SHUFFLE:
                self._update_shuffle_indices()

    def cycle_play_mode(self) -> int:
        """Cycle through play modes and return new mode"""
        self._play_mode = (self._play_mode + 1) % 4
        if self._play_mode == PLAY_MODE_SHUFFLE:
            self._update_shuffle_indices()
        return self._play_mode

    def _update_shuffle_indices(self):
        """Update shuffle order"""
        if self.songs:
            self._shuffle_indices = list(range(len(self.songs)))
            random.shuffle(self._shuffle_indices)
            self._shuffle_position = 0

    def __len__(self) -> int:
        return len(self.songs)

    def is_empty(self) -> bool:
        return len(self.songs) == 0
