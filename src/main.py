"""Traverse -- entry point."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arcade

from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE


def main():
    fullscreen = os.environ.get("LANDUS_FULLSCREEN", "0") == "1"
    arcade.open_window(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, fullscreen=fullscreen)

    from src.game_view import TitleView
    window = arcade.get_window()
    window.show_view(TitleView())
    arcade.run()


if __name__ == "__main__":
    main()
