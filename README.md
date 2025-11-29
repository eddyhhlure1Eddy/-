# Mini Music Player

A lightweight music player with modern UI built with Python.

## Features

- Modern dark/light theme UI
- Support multiple audio formats: MP3, FLAC, WAV, OGG, M4A, WMA, AAC
- Netease Cloud Music API integration
- Lyrics display
- Playlist management
- System tray support
- Global hotkeys (Windows)
- Mini mode

## Requirements

- Python 3.10+
- VLC media player (required for audio playback)

## Installation

1. Install VLC media player from https://www.videolan.org/

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Project Structure

```
mini-music-player/
├── main.py              # Entry point
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── api/                 # API modules
│   ├── netease_api.py   # Netease Cloud Music API
│   ├── lyrics_api.py    # Lyrics API
│   └── local_scanner.py # Local file scanner
├── core/                # Core modules
│   ├── audio_engine.py  # Audio playback engine
│   └── playlist.py      # Playlist management
├── ui/                  # UI modules
│   ├── main_window.py   # Main window
│   └── components/      # UI components
└── utils/               # Utilities
    ├── metadata.py      # Audio metadata
    ├── downloader.py    # Download manager
    └── tray_icon.py     # System tray
```

## Author

eddy

## License

Apache-2.0 license
