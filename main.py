# -*- coding: utf-8 -*-
"""
Mini Music Player
A lightweight music player with modern UI

Author: eddy
Version: 1.0.0
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from ui.main_window import MainWindow


def main():
    """Application entry point"""
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Create and run application
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
