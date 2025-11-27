# -*- coding: utf-8 -*-
# System Tray Icon Support
# Author: eddy

import threading
from typing import Callable, Optional

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


class TrayIcon:
    """System tray icon manager"""

    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_play_pause: Optional[Callable] = None,
        on_next: Optional[Callable] = None,
        on_prev: Optional[Callable] = None,
        on_quit: Optional[Callable] = None
    ):
        self._on_show = on_show
        self._on_play_pause = on_play_pause
        self._on_next = on_next
        self._on_prev = on_prev
        self._on_quit = on_quit

        self._icon: Optional['pystray.Icon'] = None
        self._is_running = False
        self._current_title = "No song playing"

    def start(self):
        """Start tray icon in background thread"""
        if not TRAY_AVAILABLE or self._is_running:
            return

        self._is_running = True

        def run_tray():
            image = self._create_icon_image()
            menu = self._create_menu()

            self._icon = pystray.Icon(
                "MiniPlayer",
                image,
                "Mini Music Player",
                menu
            )

            self._icon.run()

        thread = threading.Thread(target=run_tray, daemon=True)
        thread.start()

    def stop(self):
        """Stop tray icon"""
        if self._icon:
            self._icon.stop()
            self._is_running = False

    def update_title(self, title: str):
        """Update tray icon tooltip"""
        self._current_title = title
        if self._icon:
            self._icon.title = f"Mini Player - {title}"

    def _create_icon_image(self) -> 'Image.Image':
        """Create tray icon image"""
        # Create a simple music note icon
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw a circle background
        draw.ellipse([4, 4, size-4, size-4], fill=(233, 69, 96, 255))

        # Draw a simple play triangle
        points = [
            (size//3, size//4),
            (size//3, size*3//4),
            (size*3//4, size//2)
        ]
        draw.polygon(points, fill=(255, 255, 255, 255))

        return image

    def _create_menu(self) -> 'pystray.Menu':
        """Create tray context menu"""
        return pystray.Menu(
            pystray.MenuItem(
                "Show Window",
                self._handle_show,
                default=True
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Play/Pause",
                self._handle_play_pause
            ),
            pystray.MenuItem(
                "Previous",
                self._handle_prev
            ),
            pystray.MenuItem(
                "Next",
                self._handle_next
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Quit",
                self._handle_quit
            )
        )

    def _handle_show(self, icon, item):
        """Handle show window action"""
        if self._on_show:
            self._on_show()

    def _handle_play_pause(self, icon, item):
        """Handle play/pause action"""
        if self._on_play_pause:
            self._on_play_pause()

    def _handle_next(self, icon, item):
        """Handle next action"""
        if self._on_next:
            self._on_next()

    def _handle_prev(self, icon, item):
        """Handle previous action"""
        if self._on_prev:
            self._on_prev()

    def _handle_quit(self, icon, item):
        """Handle quit action"""
        self.stop()
        if self._on_quit:
            self._on_quit()

    @staticmethod
    def is_available() -> bool:
        """Check if tray icon is available"""
        return TRAY_AVAILABLE


class GlobalHotkeys:
    """Global hotkey support (Windows only)"""

    def __init__(
        self,
        on_play_pause: Optional[Callable] = None,
        on_next: Optional[Callable] = None,
        on_prev: Optional[Callable] = None,
        on_volume_up: Optional[Callable] = None,
        on_volume_down: Optional[Callable] = None
    ):
        self._on_play_pause = on_play_pause
        self._on_next = on_next
        self._on_prev = on_prev
        self._on_volume_up = on_volume_up
        self._on_volume_down = on_volume_down

        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start listening for global hotkeys"""
        try:
            import keyboard
        except ImportError:
            print("keyboard module not available for global hotkeys")
            return

        if self._running:
            return

        self._running = True

        def listen():
            try:
                # Media keys
                if self._on_play_pause:
                    keyboard.add_hotkey('play/pause media', self._on_play_pause)
                    keyboard.add_hotkey('ctrl+alt+p', self._on_play_pause)

                if self._on_next:
                    keyboard.add_hotkey('next track', self._on_next)
                    keyboard.add_hotkey('ctrl+alt+right', self._on_next)

                if self._on_prev:
                    keyboard.add_hotkey('previous track', self._on_prev)
                    keyboard.add_hotkey('ctrl+alt+left', self._on_prev)

                if self._on_volume_up:
                    keyboard.add_hotkey('ctrl+alt+up', self._on_volume_up)

                if self._on_volume_down:
                    keyboard.add_hotkey('ctrl+alt+down', self._on_volume_down)

                while self._running:
                    keyboard.wait()

            except Exception as e:
                print(f"Hotkey error: {e}")

        self._thread = threading.Thread(target=listen, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop listening for hotkeys"""
        self._running = False
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass

    @staticmethod
    def is_available() -> bool:
        """Check if global hotkeys are available"""
        try:
            import keyboard
            return True
        except ImportError:
            return False
