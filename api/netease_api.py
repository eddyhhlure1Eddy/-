# -*- coding: utf-8 -*-
# Netease Music API (Unofficial)
# Author: eddy
# Note: For educational purposes only

import requests
import hashlib
import base64
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class OnlineSong:
    """Online song data structure"""
    id: str
    name: str
    artist: str
    album: str
    duration: int  # milliseconds
    cover_url: str = ""
    play_url: str = ""


class NeteaseAPI:
    """Netease Music API client using public API endpoints"""

    # Public API endpoints (no authentication required)
    BASE_URL = "https://music.163.com/api"
    SEARCH_URL = "https://music.163.com/api/search/get"
    SONG_URL = "https://music.163.com/api/song/detail"
    LYRIC_URL = "https://music.163.com/api/song/lyric"

    # Alternative API (more reliable)
    ALT_API = "https://api.injahow.cn/meting/"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com/",
            "Accept": "application/json",
        })
        self._timeout = 10

    def search(self, keyword: str, limit: int = 20, page: int = 1) -> List[OnlineSong]:
        """
        Search for songs by keyword

        Args:
            keyword: Search keyword
            limit: Number of results per page
            page: Page number (1-based)

        Returns:
            List of OnlineSong objects
        """
        songs = []

        # Try alternative API first (more reliable)
        try:
            songs = self._search_alt_api(keyword, limit, page)
            if songs:
                return songs
        except Exception:
            pass

        # Fallback to official API
        try:
            songs = self._search_official_api(keyword, limit, page)
        except Exception as e:
            print(f"Search error: {e}")

        return songs

    def _search_alt_api(self, keyword: str, limit: int, page: int) -> List[OnlineSong]:
        """Search using alternative API"""
        songs = []

        params = {
            "type": "search",
            "search_type": "1",
            "id": keyword,
            "source": "netease",
        }

        try:
            resp = self._session.get(
                self.ALT_API,
                params=params,
                timeout=self._timeout
            )

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    for item in data[:limit]:
                        song = OnlineSong(
                            id=str(item.get("id", "")),
                            name=item.get("name", "Unknown"),
                            artist=item.get("artist", "Unknown"),
                            album=item.get("album", ""),
                            duration=int(item.get("duration", 0)) * 1000,
                            cover_url=item.get("pic", ""),
                            play_url=item.get("url", "")
                        )
                        songs.append(song)
        except Exception:
            pass

        return songs

    def _search_official_api(self, keyword: str, limit: int, page: int) -> List[OnlineSong]:
        """Search using official API"""
        songs = []
        offset = (page - 1) * limit

        params = {
            "s": keyword,
            "type": 1,  # 1 = songs
            "limit": limit,
            "offset": offset,
        }

        try:
            resp = self._session.post(
                self.SEARCH_URL,
                data=params,
                timeout=self._timeout
            )

            if resp.status_code == 200:
                data = resp.json()
                result = data.get("result", {})
                song_list = result.get("songs", [])

                for item in song_list:
                    artists = item.get("artists", [])
                    artist_name = artists[0].get("name", "Unknown") if artists else "Unknown"

                    album_info = item.get("album", {})
                    album_name = album_info.get("name", "")
                    cover_url = album_info.get("picUrl", "")

                    song = OnlineSong(
                        id=str(item.get("id", "")),
                        name=item.get("name", "Unknown"),
                        artist=artist_name,
                        album=album_name,
                        duration=item.get("duration", 0),
                        cover_url=cover_url,
                    )
                    songs.append(song)
        except Exception:
            pass

        return songs

    def get_play_url(self, song_id: str) -> Optional[str]:
        """
        Get playable URL for a song

        Args:
            song_id: Song ID

        Returns:
            Playable URL or None
        """
        # Try alternative API
        try:
            params = {
                "type": "url",
                "id": song_id,
                "source": "netease",
            }

            resp = self._session.get(
                self.ALT_API,
                params=params,
                timeout=self._timeout
            )

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    url = data[0].get("url", "")
                    if url:
                        return url
        except Exception:
            pass

        # Fallback: Direct URL (may not work for all songs)
        return f"https://music.163.com/song/media/outer/url?id={song_id}.mp3"

    def get_lyrics(self, song_id: str) -> Optional[str]:
        """
        Get lyrics for a song

        Args:
            song_id: Song ID

        Returns:
            LRC format lyrics or None
        """
        # Try alternative API
        try:
            params = {
                "type": "lrc",
                "id": song_id,
                "source": "netease",
            }

            resp = self._session.get(
                self.ALT_API,
                params=params,
                timeout=self._timeout
            )

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    lrc = data[0].get("lrc", "")
                    if lrc:
                        return lrc
        except Exception:
            pass

        # Try official API
        try:
            params = {
                "id": song_id,
                "lv": -1,
                "tv": -1,
            }

            resp = self._session.get(
                self.LYRIC_URL,
                params=params,
                timeout=self._timeout
            )

            if resp.status_code == 200:
                data = resp.json()
                lrc_data = data.get("lrc", {})
                lyric = lrc_data.get("lyric", "")
                if lyric:
                    return lyric
        except Exception:
            pass

        return None

    def get_song_detail(self, song_id: str) -> Optional[OnlineSong]:
        """
        Get detailed information for a song

        Args:
            song_id: Song ID

        Returns:
            OnlineSong object or None
        """
        try:
            params = {
                "ids": f"[{song_id}]",
            }

            resp = self._session.get(
                self.SONG_URL,
                params=params,
                timeout=self._timeout
            )

            if resp.status_code == 200:
                data = resp.json()
                songs = data.get("songs", [])

                if songs:
                    item = songs[0]
                    artists = item.get("artists", [])
                    artist_name = artists[0].get("name", "Unknown") if artists else "Unknown"

                    album_info = item.get("album", {})

                    return OnlineSong(
                        id=str(item.get("id", "")),
                        name=item.get("name", "Unknown"),
                        artist=artist_name,
                        album=album_info.get("name", ""),
                        duration=item.get("duration", 0),
                        cover_url=album_info.get("picUrl", ""),
                        play_url=self.get_play_url(song_id)
                    )
        except Exception:
            pass

        return None

    def get_cover_data(self, cover_url: str) -> Optional[bytes]:
        """
        Download cover image data

        Args:
            cover_url: Cover image URL

        Returns:
            Image bytes or None
        """
        if not cover_url:
            return None

        try:
            # Add size parameter for smaller image
            if "?" not in cover_url:
                cover_url += "?param=200y200"

            resp = self._session.get(cover_url, timeout=self._timeout)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass

        return None
