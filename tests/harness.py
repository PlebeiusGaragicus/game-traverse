"""Headless-ish driver for the real game.

arcade's true headless mode (ARCADE_HEADLESS=1) uses EGL, which exists on the
Debian cabinet but not on macOS. So: try headless, fall back to a real (small,
offscreen) window on the dev box. Either way the tests drive the real GameView,
and screenshots come out of the real framebuffer.

Import this before arcade.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyglet

pyglet.options.shadow_window = False

HEADLESS = False
if os.environ.get("ARCADE_HEADLESS") != "0":
    try:  # EGL probe: cheap, and the only reliable test
        import pyglet.libs.egl.egl  # noqa: F401

        os.environ.setdefault("ARCADE_HEADLESS", "1")
        HEADLESS = True
    except Exception:
        os.environ["ARCADE_HEADLESS"] = "0"
        os.environ.pop("ARCADE_HEADLESS", None)

import arcade
import PIL.Image

from src.config import SCREEN_HEIGHT, SCREEN_WIDTH

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")


class Harness:
    """A booted game, steppable and screenshot-able."""

    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT):
        self.window = arcade.open_window(width, height, "traverse-test")
        self.frames = 0
        self.view = None

    def show(self, view):
        self.view = view
        self.window.show_view(view)
        return self

    def game(self):
        """Jump straight into gameplay."""
        from src.game_view import GameView

        return self.show(GameView())

    def title(self):
        from src.game_view import TitleView

        return self.show(TitleView())

    # --- driving ----------------------------------------------------------

    def step(self, frames: int = 1, dt: float = 1 / 60):
        """Update + draw, i.e. one real frame."""
        for _ in range(frames):
            self.window.dispatch_events()
            self.view.on_update(dt)
            self.window.switch_to()
            self.window.dispatch_event("on_draw")
            self.window.flip()
            self.frames += 1
        return self

    def press(self, key: int, frames: int = 1):
        self.view.on_key_press(key, 0)
        self.step(frames)
        self.view.on_key_release(key, 0)
        return self

    def hold(self, key: int, frames: int, dt: float = 1 / 60):
        self.view.on_key_press(key, 0)
        self.step(frames, dt)
        return self

    def release(self, key: int):
        self.view.on_key_release(key, 0)
        return self

    # --- inspection -------------------------------------------------------

    def screenshot(self, name: str) -> str:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        self.window.switch_to()
        image = arcade.get_image(0, 0, self.window.width, self.window.height)
        image.convert("RGB").save(path)
        return path

    def image(self) -> PIL.Image.Image:
        self.window.switch_to()
        return arcade.get_image(0, 0, self.window.width, self.window.height).convert("RGB")

    def close(self):
        self.window.close()


def image_stats(image: PIL.Image.Image):
    """(distinct colors, fraction of the most common color)."""
    small = image.resize((80, 45))
    colors = small.getcolors(80 * 45) or [(small.size[0] * small.size[1], None)]
    total = sum(count for count, _ in colors)
    return len(colors), max(count for count, _ in colors) / total


def check(label: str, condition: bool, failures: list) -> bool:
    print(f"{'  OK  ' if condition else '  FAIL'} {label}")
    if not condition:
        failures.append(label)
    return condition


def report(failures: list, what: str) -> int:
    if failures:
        print(f"\n{len(failures)} FAILED in {what}:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\nall {what} checks passed  ({'headless' if HEADLESS else 'windowed'})")
    return 0
