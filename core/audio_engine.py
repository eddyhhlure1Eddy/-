# -*- coding: utf-8 -*-
# Audio Engine - VLC/Pygame based audio playback
# Author: eddy

import os
import time
from typing import Optional, Callable
from pathlib import Path

# Set VLC path for Windows
VLC_PATHS = [
    r"C:\Program Files\VideoLAN\VLC",
    r"C:\Program Files (x86)\VideoLAN\VLC",
]

for vlc_path in VLC_PATHS:
    if os.path.exists(vlc_path):
        os.environ["PATH"] = vlc_path + os.pathsep + os.environ.get("PATH", "")
        break

# Try VLC first, fallback to pygame
VLC_AVAILABLE = False
PYGAME_AVAILABLE = False

try:
    import vlc
    # Test if VLC actually works
    _test_instance = vlc.Instance()
    _test_instance.release()
    VLC_AVAILABLE = True
except Exception:
    pass

if not VLC_AVAILABLE:
    try:
        import pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        PYGAME_AVAILABLE = True
    except ImportError:
        pass


class AudioEngine:
    """Audio playback engine with VLC/Pygame support"""

    def __init__(self):
        self._current_path: Optional[str] = None
        self._volume = 70
        self._on_end_callback: Optional[Callable] = None
        self._is_playing = False
        self._paused = False
        self._duration_ms = 0
        self._start_time = 0
        self._pause_time = 0

        if VLC_AVAILABLE:
            self._init_vlc()
        elif PYGAME_AVAILABLE:
            self._init_pygame()
        else:
            raise RuntimeError("No audio backend available. Install VLC or pygame.")

        self._backend = "vlc" if VLC_AVAILABLE else "pygame"

    def _init_vlc(self):
        """Initialize VLC backend"""
        self._instance = vlc.Instance("--no-xlib")
        self._player = self._instance.media_player_new()
        self._media = None
        self._event_manager = self._player.event_manager()
        self._event_manager.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._on_vlc_end
        )

    def _init_pygame(self):
        """Initialize Pygame backend"""
        self._sound = None
        self._channel = None

    def _on_vlc_end(self, event):
        """VLC end callback"""
        self._is_playing = False
        if self._on_end_callback:
            self._on_end_callback()

    def load(self, file_path: str) -> bool:
        """Load a media file"""
        try:
            self.stop()

            # Handle URLs
            is_url = file_path.startswith("http://") or file_path.startswith("https://")

            if not is_url:
                path = Path(file_path)
                if not path.exists():
                    return False

            self._current_path = file_path

            if self._backend == "vlc":
                self._media = self._instance.media_new(file_path)
                self._player.set_media(self._media)
            else:
                # Pygame - only local files
                if is_url:
                    print("Pygame backend does not support URL streaming")
                    return False
                pygame.mixer.music.load(file_path)

            return True
        except Exception as e:
            print(f"Error loading media: {e}")
            return False

    def play(self) -> bool:
        """Start or resume playback"""
        if self._current_path is None:
            return False

        try:
            if self._backend == "vlc":
                result = self._player.play()
                time.sleep(0.1)
                self._player.audio_set_volume(self._volume)
                self._is_playing = True
                self._paused = False
                return result == 0
            else:
                pygame.mixer.music.play()
                pygame.mixer.music.set_volume(self._volume / 100)
                self._is_playing = True
                self._paused = False
                self._start_time = time.time()
                self._start_end_check()
                return True
        except Exception as e:
            print(f"Error playing: {e}")
            return False

    def _start_end_check(self):
        """Start checking for pygame end"""
        if self._backend == "pygame":
            import threading

            def check_end():
                while self._is_playing and not self._paused:
                    if not pygame.mixer.music.get_busy():
                        self._is_playing = False
                        if self._on_end_callback:
                            self._on_end_callback()
                        break
                    time.sleep(0.5)

            threading.Thread(target=check_end, daemon=True).start()

    def pause(self):
        """Pause playback"""
        if self._backend == "vlc":
            self._player.pause()
        else:
            pygame.mixer.music.pause()
            self._pause_time = time.time()

        self._paused = True

    def stop(self):
        """Stop playback"""
        if self._backend == "vlc":
            self._player.stop()
        else:
            pygame.mixer.music.stop()

        self._is_playing = False
        self._paused = False

    def toggle_pause(self):
        """Toggle play/pause state"""
        if self._paused:
            if self._backend == "vlc":
                self._player.pause()
            else:
                pygame.mixer.music.unpause()
                self._start_time += time.time() - self._pause_time
                self._start_end_check()
            self._paused = False
        elif self._is_playing:
            self.pause()

    def is_playing(self) -> bool:
        """Check if currently playing"""
        if self._backend == "vlc":
            return self._player.is_playing() == 1
        else:
            return self._is_playing and not self._paused

    def get_state(self) -> str:
        """Get current player state"""
        if self._backend == "vlc":
            state = self._player.get_state()
            state_map = {
                vlc.State.NothingSpecial: "idle",
                vlc.State.Opening: "opening",
                vlc.State.Buffering: "buffering",
                vlc.State.Playing: "playing",
                vlc.State.Paused: "paused",
                vlc.State.Stopped: "stopped",
                vlc.State.Ended: "ended",
                vlc.State.Error: "error",
            }
            return state_map.get(state, "unknown")
        else:
            if not self._is_playing:
                return "stopped"
            elif self._paused:
                return "paused"
            else:
                return "playing"

    def get_position(self) -> float:
        """Get current position (0.0 to 1.0)"""
        if self._backend == "vlc":
            pos = self._player.get_position()
            return max(0.0, min(1.0, pos)) if pos >= 0 else 0.0
        else:
            duration = self.get_duration()
            if duration <= 0:
                return 0.0
            current = self.get_time()
            return max(0.0, min(1.0, current / duration))

    def set_position(self, position: float):
        """Set playback position (0.0 to 1.0)"""
        position = max(0.0, min(1.0, position))
        if self._backend == "vlc":
            self._player.set_position(position)
        else:
            duration = self.get_duration()
            if duration > 0:
                pygame.mixer.music.set_pos(position * duration / 1000)
                self._start_time = time.time() - (position * duration / 1000)

    def get_time(self) -> int:
        """Get current time in milliseconds"""
        if self._backend == "vlc":
            t = self._player.get_time()
            return t if t >= 0 else 0
        else:
            if not self._is_playing:
                return 0
            if self._paused:
                return int((self._pause_time - self._start_time) * 1000)
            return int((time.time() - self._start_time) * 1000)

    def get_duration(self) -> int:
        """Get total duration in milliseconds"""
        if self._backend == "vlc":
            d = self._player.get_length()
            return d if d >= 0 else 0
        else:
            # Pygame doesn't provide duration easily
            # Try to get from mutagen
            if self._current_path and not self._current_path.startswith("http"):
                try:
                    from mutagen import File
                    audio = File(self._current_path)
                    if audio and audio.info:
                        return int(audio.info.length * 1000)
                except Exception:
                    pass
            return self._duration_ms

    def get_time_formatted(self) -> str:
        """Get current time as MM:SS"""
        ms = self.get_time()
        return self._format_time(ms)

    def get_duration_formatted(self) -> str:
        """Get duration as MM:SS"""
        ms = self.get_duration()
        return self._format_time(ms)

    @staticmethod
    def _format_time(ms: int) -> str:
        """Format milliseconds to MM:SS"""
        if ms <= 0:
            return "00:00"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_volume(self) -> int:
        """Get current volume (0-100)"""
        return self._volume

    def set_volume(self, volume: int):
        """Set volume (0-100)"""
        self._volume = max(0, min(100, volume))
        if self._backend == "vlc":
            self._player.audio_set_volume(self._volume)
        else:
            pygame.mixer.music.set_volume(self._volume / 100)

    def set_on_end_callback(self, callback: Callable):
        """Set callback for when playback ends"""
        self._on_end_callback = callback

    def get_current_path(self) -> Optional[str]:
        """Get path of currently loaded file"""
        return self._current_path

    def get_backend(self) -> str:
        """Get current audio backend name"""
        return self._backend

    def release(self):
        """Release resources"""
        self.stop()
        if self._backend == "vlc":
            self._player.release()
            self._instance.release()
        else:
            pygame.mixer.quit()
