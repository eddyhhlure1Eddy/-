# -*- coding: utf-8 -*-
# Local Music Scanner
# Author: eddy

import os
from pathlib import Path
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import SUPPORTED_FORMATS
from core.playlist import Song
from utils.metadata import MetadataReader


class LocalScanner:
    """Scan local directories for music files"""

    def __init__(self):
        self._stop_flag = False

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Song]:
        """
        Scan a directory for music files

        Args:
            directory: Path to scan
            recursive: Whether to scan subdirectories
            progress_callback: Callback(current, total) for progress updates

        Returns:
            List of Song objects
        """
        self._stop_flag = False
        songs = []

        # Find all music files
        music_files = self._find_music_files(directory, recursive)
        total = len(music_files)

        if total == 0:
            return songs

        # Process files with thread pool for faster metadata reading
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._create_song, f): f
                for f in music_files
            }

            completed = 0
            for future in as_completed(futures):
                if self._stop_flag:
                    break

                song = future.result()
                if song:
                    songs.append(song)

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        return songs

    def scan_file(self, file_path: str) -> Optional[Song]:
        """Scan a single file and return Song object"""
        return self._create_song(file_path)

    def stop(self):
        """Stop ongoing scan"""
        self._stop_flag = True

    def _find_music_files(self, directory: str, recursive: bool) -> List[str]:
        """Find all music files in directory"""
        files = []
        path = Path(directory)

        if not path.exists() or not path.is_dir():
            return files

        if recursive:
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    if self._is_music_file(filename):
                        files.append(os.path.join(root, filename))
        else:
            for item in path.iterdir():
                if item.is_file() and self._is_music_file(item.name):
                    files.append(str(item))

        return files

    @staticmethod
    def _is_music_file(filename: str) -> bool:
        """Check if file is a supported music format"""
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_FORMATS

    @staticmethod
    def _create_song(file_path: str) -> Optional[Song]:
        """Create a Song object from file path"""
        try:
            metadata = MetadataReader.read(file_path)
            return Song(
                path=file_path,
                title=metadata["title"],
                artist=metadata["artist"],
                album=metadata["album"],
                duration=metadata["duration"],
            )
        except Exception as e:
            print(f"Error creating song from {file_path}: {e}")
            return None

    @staticmethod
    def get_default_music_directories() -> List[str]:
        """Get common music directories for the system"""
        dirs = []

        # Windows Music folder
        user_music = Path.home() / "Music"
        if user_music.exists():
            dirs.append(str(user_music))

        # Desktop
        desktop = Path.home() / "Desktop"
        if desktop.exists():
            dirs.append(str(desktop))

        # Downloads
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            dirs.append(str(downloads))

        return dirs
