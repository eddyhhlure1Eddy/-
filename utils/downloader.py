# -*- coding: utf-8 -*-
# Download and Cache Manager
# Author: eddy

import os
import json
import hashlib
import threading
import requests
from pathlib import Path
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime

from config import CACHE_DIR


@dataclass
class CachedSong:
    """Cached song metadata"""
    id: str
    name: str
    artist: str
    album: str
    duration: int
    local_path: str
    source: str  # "netease", "local", etc.
    cached_at: str
    cover_path: Optional[str] = None


class DownloadManager:
    """Manage song downloads and cache"""

    CACHE_INDEX_FILE = "cache_index.json"
    MAX_CACHE_SIZE_MB = 500  # Max cache size in MB

    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir or CACHE_DIR
        self._cache_dir.mkdir(exist_ok=True)

        self._songs_dir = self._cache_dir / "songs"
        self._covers_dir = self._cache_dir / "covers"
        self._songs_dir.mkdir(exist_ok=True)
        self._covers_dir.mkdir(exist_ok=True)

        self._cache_index: Dict[str, CachedSong] = {}
        self._download_queue: List[dict] = []
        self._is_downloading = False
        self._lock = threading.Lock()

        self._load_cache_index()

    def _load_cache_index(self):
        """Load cache index from file"""
        index_path = self._cache_dir / self.CACHE_INDEX_FILE
        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for song_id, song_data in data.items():
                        self._cache_index[song_id] = CachedSong(**song_data)
            except Exception as e:
                print(f"Error loading cache index: {e}")

    def _save_cache_index(self):
        """Save cache index to file"""
        index_path = self._cache_dir / self.CACHE_INDEX_FILE
        try:
            data = {
                song_id: asdict(song)
                for song_id, song in self._cache_index.items()
            }
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cache index: {e}")

    def is_cached(self, song_id: str) -> bool:
        """Check if a song is cached"""
        if song_id in self._cache_index:
            cached = self._cache_index[song_id]
            return Path(cached.local_path).exists()
        return False

    def get_cached_path(self, song_id: str) -> Optional[str]:
        """Get local path of cached song"""
        if self.is_cached(song_id):
            return self._cache_index[song_id].local_path
        return None

    def get_cached_song(self, song_id: str) -> Optional[CachedSong]:
        """Get cached song metadata"""
        if song_id in self._cache_index:
            return self._cache_index[song_id]
        return None

    def download(
        self,
        song_id: str,
        url: str,
        name: str,
        artist: str,
        album: str = "",
        duration: int = 0,
        cover_url: Optional[str] = None,
        source: str = "netease",
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """
        Download a song to cache

        Args:
            song_id: Unique song ID
            url: Download URL
            name: Song name
            artist: Artist name
            album: Album name
            duration: Duration in ms
            cover_url: Cover image URL
            source: Source identifier
            on_progress: Progress callback(downloaded, total)
            on_complete: Complete callback(local_path)
            on_error: Error callback(error_message)
        """
        task = {
            "song_id": song_id,
            "url": url,
            "name": name,
            "artist": artist,
            "album": album,
            "duration": duration,
            "cover_url": cover_url,
            "source": source,
            "on_progress": on_progress,
            "on_complete": on_complete,
            "on_error": on_error
        }

        with self._lock:
            self._download_queue.append(task)

        self._process_queue()

    def _process_queue(self):
        """Process download queue"""
        with self._lock:
            if self._is_downloading or not self._download_queue:
                return
            self._is_downloading = True
            task = self._download_queue.pop(0)

        def download_thread():
            try:
                self._download_song(task)
            finally:
                with self._lock:
                    self._is_downloading = False
                self._process_queue()

        threading.Thread(target=download_thread, daemon=True).start()

    def _download_song(self, task: dict):
        """Download a single song"""
        song_id = task["song_id"]
        url = task["url"]
        on_progress = task.get("on_progress")
        on_complete = task.get("on_complete")
        on_error = task.get("on_error")

        # Check if already cached
        if self.is_cached(song_id):
            if on_complete:
                on_complete(self.get_cached_path(song_id))
            return

        # Generate filename
        safe_name = self._safe_filename(f"{task['artist']} - {task['name']}")
        ext = self._get_extension(url)
        filename = f"{song_id}_{safe_name}{ext}"
        local_path = self._songs_dir / filename

        try:
            # Download with progress
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if on_progress and total_size > 0:
                            on_progress(downloaded, total_size)

            # Download cover if available
            cover_path = None
            if task.get("cover_url"):
                cover_path = self._download_cover(song_id, task["cover_url"])

            # Add to cache index
            cached_song = CachedSong(
                id=song_id,
                name=task["name"],
                artist=task["artist"],
                album=task["album"],
                duration=task["duration"],
                local_path=str(local_path),
                source=task["source"],
                cached_at=datetime.now().isoformat(),
                cover_path=cover_path
            )

            self._cache_index[song_id] = cached_song
            self._save_cache_index()

            if on_complete:
                on_complete(str(local_path))

        except Exception as e:
            # Clean up partial download
            if local_path.exists():
                local_path.unlink()

            if on_error:
                on_error(str(e))

    def _download_cover(self, song_id: str, cover_url: str) -> Optional[str]:
        """Download cover image"""
        try:
            ext = self._get_extension(cover_url) or ".jpg"
            cover_path = self._covers_dir / f"{song_id}{ext}"

            response = requests.get(cover_url, timeout=10)
            response.raise_for_status()

            with open(cover_path, 'wb') as f:
                f.write(response.content)

            return str(cover_path)
        except Exception:
            return None

    def get_all_cached(self) -> List[CachedSong]:
        """Get all cached songs"""
        return list(self._cache_index.values())

    def get_cache_size(self) -> int:
        """Get total cache size in bytes"""
        total = 0
        for path in self._songs_dir.iterdir():
            if path.is_file():
                total += path.stat().st_size
        for path in self._covers_dir.iterdir():
            if path.is_file():
                total += path.stat().st_size
        return total

    def get_cache_size_mb(self) -> float:
        """Get cache size in MB"""
        return self.get_cache_size() / (1024 * 1024)

    def remove_cached(self, song_id: str) -> bool:
        """Remove a cached song"""
        if song_id not in self._cache_index:
            return False

        cached = self._cache_index[song_id]

        # Remove files
        try:
            local_path = Path(cached.local_path)
            if local_path.exists():
                local_path.unlink()

            if cached.cover_path:
                cover_path = Path(cached.cover_path)
                if cover_path.exists():
                    cover_path.unlink()
        except Exception:
            pass

        # Remove from index
        del self._cache_index[song_id]
        self._save_cache_index()

        return True

    def clear_cache(self):
        """Clear all cached songs"""
        # Remove all files
        for path in self._songs_dir.iterdir():
            try:
                path.unlink()
            except Exception:
                pass

        for path in self._covers_dir.iterdir():
            try:
                path.unlink()
            except Exception:
                pass

        # Clear index
        self._cache_index.clear()
        self._save_cache_index()

    def cleanup_old(self, max_age_days: int = 30):
        """Remove cached songs older than max_age_days"""
        cutoff = datetime.now()
        to_remove = []

        for song_id, cached in self._cache_index.items():
            try:
                cached_at = datetime.fromisoformat(cached.cached_at)
                age = (cutoff - cached_at).days
                if age > max_age_days:
                    to_remove.append(song_id)
            except Exception:
                pass

        for song_id in to_remove:
            self.remove_cached(song_id)

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Create safe filename"""
        # Remove/replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name[:50]  # Limit length

    @staticmethod
    def _get_extension(url: str) -> str:
        """Get file extension from URL"""
        # Remove query parameters
        url = url.split('?')[0]
        ext = Path(url).suffix.lower()
        if ext in ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac']:
            return ext
        return '.mp3'  # Default
