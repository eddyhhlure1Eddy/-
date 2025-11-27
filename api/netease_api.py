# -*- coding: utf-8 -*-
# Netease Music API (Unofficial)
# Author: eddy
# Note: For educational purposes only

import requests
import hashlib
import base64
import json
import random
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

    # Multiple backup APIs for reliability
    METING_APIS = [
        "https://api.injahow.cn/meting/",
        "https://meting.qjqq.cn/",
        "https://api.i-meto.com/meting/api",
    ]

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://music.163.com/",
            "Accept": "application/json, text/plain, */*",
        })
        self._timeout = 15
        self._working_api = None

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

        # Try meting APIs first (more reliable for play URLs)
        songs = self._search_meting_api(keyword, limit, page)
        if songs:
            return songs

        # Fallback to official API
        try:
            songs = self._search_official_api(keyword, limit, page)
        except Exception as e:
            print(f"Search error: {e}")

        return songs

    def _search_meting_api(self, keyword: str, limit: int, page: int) -> List[OnlineSong]:
        """Search using meting APIs with fallback"""
        songs = []

        # Use working API first if available
        apis_to_try = list(self.METING_APIS)
        if self._working_api and self._working_api in apis_to_try:
            apis_to_try.remove(self._working_api)
            apis_to_try.insert(0, self._working_api)

        for api_url in apis_to_try:
            try:
                params = {
                    "type": "search",
                    "id": keyword,
                    "server": "netease",
                }

                resp = self._session.get(
                    api_url,
                    params=params,
                    timeout=self._timeout
                )

                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        self._working_api = api_url
                        for item in data[:limit]:
                            song = OnlineSong(
                                id=str(item.get("id", item.get("url_id", ""))),
                                name=item.get("name", item.get("title", "Unknown")),
                                artist=item.get("artist", item.get("author", "Unknown")),
                                album=item.get("album", ""),
                                duration=int(float(item.get("duration", 0))) * 1000,
                                cover_url=item.get("pic", item.get("cover", "")),
                                play_url=item.get("url", "")
                            )
                            songs.append(song)
                        return songs
            except Exception:
                continue

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
        # Try meting APIs with fallback
        apis_to_try = list(self.METING_APIS)
        if self._working_api and self._working_api in apis_to_try:
            apis_to_try.remove(self._working_api)
            apis_to_try.insert(0, self._working_api)

        for api_url in apis_to_try:
            try:
                params = {
                    "type": "url",
                    "id": song_id,
                    "server": "netease",
                }

                resp = self._session.get(
                    api_url,
                    params=params,
                    timeout=self._timeout
                )

                if resp.status_code == 200:
                    data = resp.json()
                    url = None
                    if isinstance(data, list) and data:
                        url = data[0].get("url", "")
                    elif isinstance(data, dict):
                        url = data.get("url", "")

                    if url and self._validate_url(url):
                        self._working_api = api_url
                        return url
            except Exception:
                continue

        # Fallback: Direct URL (may not work for VIP songs)
        direct_url = f"https://music.163.com/song/media/outer/url?id={song_id}.mp3"
        if self._validate_url(direct_url):
            return direct_url

        return None

    def _validate_url(self, url: str) -> bool:
        """Check if URL is accessible"""
        if not url or not url.startswith("http"):
            return False
        try:
            resp = self._session.head(url, timeout=5, allow_redirects=True)
            return resp.status_code == 200
        except Exception:
            return True  # Assume valid if can't check

    def get_lyrics(self, song_id: str) -> Optional[str]:
        """
        Get lyrics for a song

        Args:
            song_id: Song ID

        Returns:
            LRC format lyrics or None
        """
        # Try meting APIs
        apis_to_try = list(self.METING_APIS)
        if self._working_api and self._working_api in apis_to_try:
            apis_to_try.remove(self._working_api)
            apis_to_try.insert(0, self._working_api)

        for api_url in apis_to_try:
            try:
                params = {
                    "type": "lrc",
                    "id": song_id,
                    "server": "netease",
                }

                resp = self._session.get(
                    api_url,
                    params=params,
                    timeout=self._timeout
                )

                if resp.status_code == 200:
                    data = resp.json()
                    lrc = None
                    if isinstance(data, list) and data:
                        lrc = data[0].get("lrc", data[0].get("lyric", ""))
                    elif isinstance(data, dict):
                        lrc = data.get("lrc", data.get("lyric", ""))

                    if lrc:
                        self._working_api = api_url
                        return lrc
            except Exception:
                continue

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

    def get_mood_playlist(self, mood: str, limit: int = 30) -> List[OnlineSong]:
        """
        Get songs based on mood

        Args:
            mood: Mood keyword (happy, sad, relaxed, energetic, romantic, focus)
            limit: Number of songs to fetch

        Returns:
            List of OnlineSong objects
        """
        # Mood to search keyword mapping
        mood_keywords = {
            "happy": ["happy", "upbeat", "cheerful", "joy"],
            "sad": ["sad", "melancholy", "heartbreak", "lonely"],
            "relaxed": ["chill", "peaceful", "calm", "lofi"],
            "energetic": ["rock", "workout", "hype", "dance"],
            "romantic": ["love", "romantic", "sweet", "ballad"],
            "focus": ["study", "piano", "instrumental", "classical"],
        }

        keywords = mood_keywords.get(mood.lower(), [mood])
        keyword = random.choice(keywords)

        songs = self.search(keyword, limit=limit)
        if songs:
            random.shuffle(songs)
        return songs

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
