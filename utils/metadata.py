# -*- coding: utf-8 -*-
# Music Metadata Reader
# Author: eddy

from pathlib import Path
from typing import Optional, Dict, Any
import io

try:
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.id3 import ID3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class MetadataReader:
    """Read metadata from audio files"""

    @staticmethod
    def read(file_path: str) -> Dict[str, Any]:
        """
        Read metadata from an audio file

        Returns dict with keys:
        - title: str
        - artist: str
        - album: str
        - duration: int (milliseconds)
        - cover_data: bytes or None
        """
        result = {
            "title": Path(file_path).stem,
            "artist": "Unknown Artist",
            "album": "Unknown Album",
            "duration": 0,
            "cover_data": None,
        }

        if not MUTAGEN_AVAILABLE:
            return result

        try:
            audio = MutagenFile(file_path)
            if audio is None:
                return result

            # Get duration
            if hasattr(audio, "info") and hasattr(audio.info, "length"):
                result["duration"] = int(audio.info.length * 1000)

            # Get tags based on file type
            ext = Path(file_path).suffix.lower()

            if ext == ".mp3":
                result.update(MetadataReader._read_mp3(file_path))
            elif ext == ".flac":
                result.update(MetadataReader._read_flac(file_path))
            else:
                result.update(MetadataReader._read_generic(audio))

        except Exception as e:
            print(f"Error reading metadata: {e}")

        return result

    @staticmethod
    def _read_mp3(file_path: str) -> Dict[str, Any]:
        """Read MP3 specific metadata"""
        result = {}
        try:
            audio = MP3(file_path)
            tags = audio.tags

            if tags:
                # Title
                if "TIT2" in tags:
                    result["title"] = str(tags["TIT2"])

                # Artist
                if "TPE1" in tags:
                    result["artist"] = str(tags["TPE1"])
                elif "TPE2" in tags:
                    result["artist"] = str(tags["TPE2"])

                # Album
                if "TALB" in tags:
                    result["album"] = str(tags["TALB"])

                # Cover art
                for key in tags.keys():
                    if key.startswith("APIC"):
                        result["cover_data"] = tags[key].data
                        break
        except Exception:
            pass

        return result

    @staticmethod
    def _read_flac(file_path: str) -> Dict[str, Any]:
        """Read FLAC specific metadata"""
        result = {}
        try:
            audio = FLAC(file_path)

            if "title" in audio:
                result["title"] = audio["title"][0]
            if "artist" in audio:
                result["artist"] = audio["artist"][0]
            if "album" in audio:
                result["album"] = audio["album"][0]

            # Cover art
            if audio.pictures:
                result["cover_data"] = audio.pictures[0].data
        except Exception:
            pass

        return result

    @staticmethod
    def _read_generic(audio) -> Dict[str, Any]:
        """Read generic audio file metadata"""
        result = {}
        try:
            tags = audio.tags
            if tags:
                # Try common tag names
                for title_key in ["title", "TITLE", "Title"]:
                    if title_key in tags:
                        result["title"] = str(tags[title_key][0])
                        break

                for artist_key in ["artist", "ARTIST", "Artist"]:
                    if artist_key in tags:
                        result["artist"] = str(tags[artist_key][0])
                        break

                for album_key in ["album", "ALBUM", "Album"]:
                    if album_key in tags:
                        result["album"] = str(tags[album_key][0])
                        break
        except Exception:
            pass

        return result

    @staticmethod
    def extract_cover_image(cover_data: bytes, size: tuple = (100, 100)) -> Optional[Any]:
        """
        Extract and resize cover image from bytes
        Returns PIL Image or None
        """
        if not PIL_AVAILABLE or cover_data is None:
            return None

        try:
            image = Image.open(io.BytesIO(cover_data))
            image.thumbnail(size, Image.Resampling.LANCZOS)
            return image
        except Exception:
            return None
