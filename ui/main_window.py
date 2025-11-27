# -*- coding: utf-8 -*-
# Main Window with Full Features
# Author: eddy

import customtkinter as ctk
from tkinter import filedialog
from typing import Optional
import threading
import random

from config import (
    APP_NAME,
    CURRENT_THEME,
    SUPPORTED_FORMATS
)
from core.audio_engine import AudioEngine
from core.playlist import Playlist, Song
from api.local_scanner import LocalScanner
from api.netease_api import NeteaseAPI, OnlineSong
from utils.metadata import MetadataReader
from utils.downloader import DownloadManager
from utils.tray_icon import TrayIcon, GlobalHotkeys
from ui.components import (
    PlayerControls,
    ProgressBar,
    VolumeSlider,
    SongInfo,
    PlaylistPanel,
    SearchPanel,
    MiniLyricsDisplay,
    SettingsPanel,
    SettingsManager
)


class MainWindow(ctk.CTk):
    """Main application window with full features"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title(APP_NAME)
        self.geometry("480x600")
        self.minsize(450, 520)
        self.configure(fg_color=CURRENT_THEME["bg_primary"])

        # Core components
        self._engine = AudioEngine()
        self._playlist = Playlist()
        self._scanner = LocalScanner()
        self._netease = NeteaseAPI()
        self._downloader = DownloadManager()
        self._settings = SettingsManager()

        # System tray
        self._tray = TrayIcon(
            on_show=self._show_window,
            on_play_pause=self._on_play_pause,
            on_next=self._on_next,
            on_prev=self._on_prev,
            on_quit=self._quit_app
        )

        # Global hotkeys
        self._hotkeys = GlobalHotkeys(
            on_play_pause=self._on_play_pause,
            on_next=self._on_next,
            on_prev=self._on_prev,
            on_volume_up=lambda: self._adjust_volume(5),
            on_volume_down=lambda: self._adjust_volume(-5)
        )

        # State
        self._update_job = None
        self._current_cover_data = None
        self._current_online_song: Optional[OnlineSong] = None
        self._settings_window: Optional[SettingsPanel] = None

        # Setup
        self._create_widgets()
        self._bind_events()
        self._start_update_loop()
        self._start_tray()
        self._start_hotkeys()

        # Restore settings
        self._restore_settings()

        # Handle window events
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Unmap>", self._on_minimize)

    def _create_widgets(self):
        """Create main window widgets"""
        theme = CURRENT_THEME

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header with settings button
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))

        # App title
        ctk.CTkLabel(
            header_frame,
            text=APP_NAME,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=theme["text_primary"]
        ).pack(side="left")

        # Settings button
        self.btn_settings = ctk.CTkButton(
            header_frame,
            text="\u2699",  # Gear icon
            width=32,
            height=32,
            corner_radius=16,
            fg_color="transparent",
            hover_color=theme["button_hover"],
            text_color=theme["text_secondary"],
            font=ctk.CTkFont(size=18),
            command=self._open_settings
        )
        self.btn_settings.pack(side="right")

        # Song info
        self.song_info = SongInfo(main_frame)
        self.song_info.pack(fill="x", pady=(5, 5))

        # Mini lyrics display
        self.mini_lyrics = MiniLyricsDisplay(main_frame)
        self.mini_lyrics.pack(fill="x", pady=(0, 5))

        # Progress bar
        self.progress_bar = ProgressBar(
            main_frame,
            on_seek=self._on_seek
        )
        self.progress_bar.pack(fill="x", pady=5)

        # Controls section
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=5)

        # Player controls
        self.player_controls = PlayerControls(
            controls_frame,
            on_prev=self._on_prev,
            on_play_pause=self._on_play_pause,
            on_next=self._on_next,
            on_mode_change=self._on_mode_change
        )
        self.player_controls.pack(side="left", expand=True)

        # Volume slider
        self.volume_slider = VolumeSlider(
            main_frame,
            on_volume_change=self._on_volume_change
        )
        self.volume_slider.pack(fill="x", pady=(5, 10))

        # Tabview
        self.tabview = ctk.CTkTabview(
            main_frame,
            fg_color=theme["bg_secondary"],
            segmented_button_fg_color=theme["bg_tertiary"],
            segmented_button_selected_color=theme["accent"],
            segmented_button_selected_hover_color=theme["button_hover"],
            segmented_button_unselected_color=theme["bg_tertiary"],
            segmented_button_unselected_hover_color=theme["button_hover"]
        )
        self.tabview.pack(fill="both", expand=True)

        # Tabs
        tab_playlist = self.tabview.add("Playlist")
        tab_search = self.tabview.add("Search")
        tab_cache = self.tabview.add("Cache")

        # --- Playlist Tab ---
        playlist_container = ctk.CTkFrame(tab_playlist, fg_color="transparent")
        playlist_container.pack(fill="both", expand=True)

        btn_frame = ctk.CTkFrame(playlist_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 10))

        btn_style = {
            "width": 80,
            "height": 28,
            "corner_radius": 14,
            "fg_color": theme["bg_tertiary"],
            "hover_color": theme["button_hover"],
            "text_color": theme["text_primary"],
            "font": ctk.CTkFont(size=11)
        }

        ctk.CTkButton(
            btn_frame, text="Open File",
            command=self._open_file, **btn_style
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            btn_frame, text="Open Folder",
            command=self._open_folder, **btn_style
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            btn_frame, text="Clear",
            command=self._clear_playlist, **btn_style
        ).pack(side="left", padx=3)

        self.playlist_panel = PlaylistPanel(
            playlist_container,
            on_song_double_click=self._on_song_double_click
        )
        self.playlist_panel.pack(fill="both", expand=True)

        # --- Search Tab ---
        self.search_panel = SearchPanel(
            tab_search,
            on_song_play=self._on_online_song_play,
            on_song_add=self._on_online_song_add
        )
        self.search_panel.pack(fill="both", expand=True)

        # --- Cache Tab ---
        self._create_cache_tab(tab_cache)

    def _create_cache_tab(self, parent):
        """Create cache management tab"""
        theme = CURRENT_THEME

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Cache info
        self.lbl_cache_info = ctk.CTkLabel(
            container,
            text="Calculating cache size...",
            font=ctk.CTkFont(size=12),
            text_color=theme["text_secondary"]
        )
        self.lbl_cache_info.pack(pady=10)

        # Clear cache button
        ctk.CTkButton(
            container,
            text="Clear All Cache",
            width=120,
            height=32,
            corner_radius=16,
            fg_color=theme["accent"],
            hover_color=theme["button_hover"],
            command=self._clear_cache
        ).pack(pady=10)

        # Cached songs list
        ctk.CTkLabel(
            container,
            text="Cached Songs",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme["text_primary"]
        ).pack(anchor="w", pady=(20, 5))

        self.cache_list = ctk.CTkScrollableFrame(
            container,
            fg_color=theme["bg_tertiary"],
            corner_radius=8
        )
        self.cache_list.pack(fill="both", expand=True)

        # Update cache info
        self._update_cache_display()

    def _update_cache_display(self):
        """Update cache information display"""
        size_mb = self._downloader.get_cache_size_mb()
        cached = self._downloader.get_all_cached()

        self.lbl_cache_info.configure(
            text=f"Cache: {size_mb:.1f} MB | {len(cached)} songs"
        )

        # Clear list
        for widget in self.cache_list.winfo_children():
            widget.destroy()

        theme = CURRENT_THEME

        # Add cached songs
        for song in cached:
            frame = ctk.CTkFrame(self.cache_list, fg_color="transparent")
            frame.pack(fill="x", pady=2)

            ctk.CTkLabel(
                frame,
                text=f"{song.name} - {song.artist}",
                font=ctk.CTkFont(size=11),
                text_color=theme["text_primary"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkButton(
                frame,
                text="X",
                width=24,
                height=24,
                corner_radius=12,
                fg_color="transparent",
                hover_color=theme["button_hover"],
                text_color=theme["text_secondary"],
                command=lambda s=song: self._remove_cached(s.id)
            ).pack(side="right")

    def _remove_cached(self, song_id: str):
        """Remove a cached song"""
        self._downloader.remove_cached(song_id)
        self._update_cache_display()

    def _clear_cache(self):
        """Clear all cache"""
        self._downloader.clear_cache()
        self._update_cache_display()

    def _bind_events(self):
        """Bind keyboard shortcuts"""
        self.bind("<space>", lambda e: self._on_play_pause())
        self.bind("<Left>", lambda e: self._on_prev())
        self.bind("<Right>", lambda e: self._on_next())
        self.bind("<Up>", lambda e: self._adjust_volume(5))
        self.bind("<Down>", lambda e: self._adjust_volume(-5))
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<Control-comma>", lambda e: self._open_settings())
        self.bind("<Escape>", lambda e: self._minimize_to_tray())

        self._engine.set_on_end_callback(self._on_song_end)

    def _start_tray(self):
        """Start system tray icon"""
        if TrayIcon.is_available():
            self._tray.start()

    def _start_hotkeys(self):
        """Start global hotkeys"""
        if GlobalHotkeys.is_available():
            self._hotkeys.start()

    def _restore_settings(self):
        """Restore saved settings"""
        volume = self._settings.get("volume", 70)
        self.volume_slider.set_volume(volume)
        self._engine.set_volume(volume)

        play_mode = self._settings.get("play_mode", 0)
        self._playlist.set_play_mode(play_mode)
        self.player_controls.set_play_mode(play_mode)

    def _focus_search(self):
        """Focus search tab"""
        self.tabview.set("Search")
        self.search_panel.focus_search()

    def _open_settings(self):
        """Open settings dialog"""
        if self._settings_window is None or not self._settings_window.winfo_exists():
            self._settings_window = SettingsPanel(
                self,
                self._settings,
                on_theme_change=self._on_theme_change,
                on_cache_clear=self._clear_cache
            )

    def _on_theme_change(self, theme_name: str):
        """Handle theme change"""
        ctk.set_appearance_mode(theme_name)

    def _start_update_loop(self):
        """Start UI update loop"""
        self._update_ui()

    def _update_ui(self):
        """Update UI elements"""
        if self._engine.is_playing():
            position = self._engine.get_position()
            current_time = self._engine.get_time()

            self.progress_bar.set_position(position)
            self.progress_bar.set_current_time(self._engine.get_time_formatted())

            if self.mini_lyrics.has_lyrics():
                self.mini_lyrics.update_display(current_time)

        self._update_job = self.after(100, self._update_ui)

    def _on_play_pause(self):
        """Handle play/pause"""
        if self._playlist.is_empty():
            # Auto-load random mood playlist
            self._load_random_mood_playlist()
            return

        if self._engine.get_current_path() is None:
            song = self._playlist.get_current_song()
            if song is None:
                self._playlist.set_current_index(0)
                song = self._playlist.get_current_song()
            if song:
                self._play_song(song)
        else:
            self._engine.toggle_pause()
            self.player_controls.set_playing(self._engine.is_playing())

    def _load_random_mood_playlist(self):
        """Load a random mood playlist and start playing"""
        moods = ["happy", "sad", "relaxed", "energetic", "romantic", "focus"]
        mood = random.choice(moods)

        self.song_info.update_info(
            title=f"Loading {mood.capitalize()} playlist...",
            artist="Please wait",
            album="",
            cover_data=None
        )

        def load_thread():
            songs = self._netease.get_mood_playlist(mood, limit=30)
            if songs:
                self.after(0, lambda: self._start_mood_playback(songs))
            else:
                self.after(0, lambda: self.song_info.update_info(
                    title="Failed to load",
                    artist="Check network",
                    album="",
                    cover_data=None
                ))

        threading.Thread(target=load_thread, daemon=True).start()

    def _start_mood_playback(self, online_songs: list):
        """Start playing the mood playlist"""
        if not online_songs:
            return

        # Clear current playlist
        self._playlist.clear()
        self.playlist_panel.clear()

        # Get URLs and add all songs to playlist
        added_count = 0
        for online_song in online_songs:
            if not online_song.play_url:
                online_song.play_url = self._netease.get_play_url(online_song.id)
            if online_song.play_url:
                song = Song(
                    path=online_song.play_url,
                    title=online_song.name,
                    artist=online_song.artist,
                    album=online_song.album,
                    duration=online_song.duration
                )
                self._playlist.add_song(song)
                added_count += 1

        # Update playlist panel
        self.playlist_panel.set_songs(self._playlist.songs)

        # Start playing first song
        if not self._playlist.is_empty():
            self._playlist.set_current_index(0)
            song = self._playlist.get_current_song()
            if song:
                self._play_song(song)
                self.playlist_panel.select_song(0)

        # Switch to playlist tab
        self.tabview.set("Playlist")

    def _on_prev(self):
        """Handle previous"""
        song = self._playlist.previous_song()
        if song:
            self._play_song(song)
            self.playlist_panel.select_song(self._playlist.get_current_index())

    def _on_next(self):
        """Handle next"""
        song = self._playlist.next_song()
        if song:
            self._play_song(song)
            self.playlist_panel.select_song(self._playlist.get_current_index())

    def _on_seek(self, position: float):
        """Handle seek"""
        self._engine.set_position(position)

    def _on_volume_change(self, volume: int):
        """Handle volume change"""
        self._engine.set_volume(volume)
        self._settings.set("volume", volume)

    def _adjust_volume(self, delta: int):
        """Adjust volume"""
        current = self.volume_slider.get_volume()
        new_volume = max(0, min(100, current + delta))
        self.volume_slider.set_volume(new_volume)
        self._engine.set_volume(new_volume)

    def _on_mode_change(self, mode: int):
        """Handle play mode change"""
        self._playlist.set_play_mode(mode)
        self._settings.set("play_mode", mode)

    def _on_song_end(self):
        """Handle song end"""
        self.after(0, self._play_next_on_end)

    def _play_next_on_end(self):
        """Play next song"""
        song = self._playlist.next_song()
        if song:
            self._play_song(song)
            self.playlist_panel.select_song(self._playlist.get_current_index())
        else:
            self.player_controls.set_playing(False)
            self.progress_bar.reset()

    def _on_song_double_click(self, index: int):
        """Handle playlist double click"""
        self._playlist.set_current_index(index)
        song = self._playlist.get_current_song()
        if song:
            self._play_song(song)

    def _play_song(self, song: Song):
        """Play a song"""
        self._current_online_song = None

        if self._engine.load(song.path):
            self._engine.play()
            self.player_controls.set_playing(True)

            metadata = MetadataReader.read(song.path)
            self._current_cover_data = metadata.get("cover_data")

            self.song_info.update_info(
                title=song.title,
                artist=song.artist,
                album=song.album,
                cover_data=self._current_cover_data
            )

            self._tray.update_title(f"{song.title} - {song.artist}")

            duration = self._engine.get_duration()
            if duration > 0:
                self.progress_bar.set_duration(
                    self._engine.get_duration_formatted(),
                    duration
                )

            self.mini_lyrics.clear()

    def _on_online_song_play(self, online_song: OnlineSong):
        """Play online song"""
        if not online_song.play_url:
            return

        self._current_online_song = online_song

        # Check cache first
        cached_path = self._downloader.get_cached_path(online_song.id)
        play_url = cached_path if cached_path else online_song.play_url

        if self._engine.load(play_url):
            self._engine.play()
            self.player_controls.set_playing(True)

            self.song_info.update_info(
                title=online_song.name,
                artist=online_song.artist,
                album=online_song.album,
                cover_data=None
            )

            self._tray.update_title(f"{online_song.name} - {online_song.artist}")

            if online_song.cover_url:
                def load_cover():
                    cover_data = self._netease.get_cover_data(online_song.cover_url)
                    if cover_data:
                        self.after(0, lambda: self.song_info.update_info(
                            title=online_song.name,
                            artist=online_song.artist,
                            album=online_song.album,
                            cover_data=cover_data
                        ))
                threading.Thread(target=load_cover, daemon=True).start()

            self.after(500, self._update_online_duration)
            self.mini_lyrics.load_lyrics(online_song.id)

            # Cache in background if enabled
            if self._settings.get("cache_enabled", True) and not cached_path:
                self._downloader.download(
                    song_id=online_song.id,
                    url=online_song.play_url,
                    name=online_song.name,
                    artist=online_song.artist,
                    album=online_song.album,
                    duration=online_song.duration,
                    cover_url=online_song.cover_url,
                    on_complete=lambda p: self._update_cache_display()
                )

    def _update_online_duration(self):
        """Update duration for online song"""
        duration = self._engine.get_duration()
        if duration > 0:
            self.progress_bar.set_duration(
                self._engine.get_duration_formatted(),
                duration
            )

    def _on_online_song_add(self, online_song: OnlineSong):
        """Add online song to playlist"""
        if not online_song.play_url:
            return

        song = Song(
            path=online_song.play_url,
            title=online_song.name,
            artist=online_song.artist,
            album=online_song.album,
            duration=online_song.duration
        )

        self._playlist.add_song(song)
        self.playlist_panel.set_songs(self._playlist.songs)
        self.tabview.set("Playlist")

    def _open_file(self):
        """Open file dialog"""
        filetypes = [
            ("Audio Files", " ".join(f"*{ext}" for ext in SUPPORTED_FORMATS)),
            ("All Files", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Select Audio Files", filetypes=filetypes)
        if files:
            self._add_files(list(files))

    def _open_folder(self):
        """Open folder dialog"""
        folder = filedialog.askdirectory(title="Select Music Folder")
        if folder:
            def scan():
                songs = self._scanner.scan_directory(folder)
                self.after(0, lambda: self._add_songs(songs))
            threading.Thread(target=scan, daemon=True).start()

    def _add_files(self, files: list):
        """Add files to playlist"""
        for f in files:
            song = self._scanner.scan_file(f)
            if song:
                self._playlist.add_song(song)
        self.playlist_panel.set_songs(self._playlist.songs)

    def _add_songs(self, songs: list):
        """Add songs to playlist"""
        self._playlist.add_songs(songs)
        self.playlist_panel.set_songs(self._playlist.songs)

    def _clear_playlist(self):
        """Clear playlist"""
        self._engine.stop()
        self._playlist.clear()
        self.playlist_panel.clear()
        self.song_info.clear()
        self.progress_bar.reset()
        self.player_controls.set_playing(False)
        self.mini_lyrics.clear()

    def _minimize_to_tray(self):
        """Minimize to system tray"""
        if TrayIcon.is_available():
            self.withdraw()

    def _show_window(self):
        """Show window from tray"""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_minimize(self, event):
        """Handle window minimize"""
        pass  # Could auto-minimize to tray

    def _quit_app(self):
        """Quit application"""
        self._on_close()

    def _on_close(self):
        """Handle window close"""
        if self._update_job:
            self.after_cancel(self._update_job)
        self._tray.stop()
        self._hotkeys.stop()
        self._engine.release()
        self.destroy()
