"""Screen capture: run with `.venv/bin/python tests/test_screens.py`.

Renders every screen and state to tests/screenshots/. Assertions only catch a
blank or frozen frame -- **open the PNGs and look at them**. Whether the maze
reads well is a human judgement.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from harness import SCREENSHOT_DIR, Harness, check, image_stats, report  # noqa: E402

import arcade  # noqa: E402

from src.map_data import LEVELS  # noqa: E402


def capture(h, name, failures, min_colors=8, max_uniform=0.995):
    """A blank frame is 1 color at 100% uniform. Text on flat colour is
    legitimately ~98%, so this only asserts that something was drawn."""
    path = h.screenshot(name)
    colors, uniform = image_stats(h.image())
    check(f"{name}: rendered something ({colors} colors, {uniform:.0%} most-common)"
          f" -> {path.split('/')[-1]}",
          colors >= min_colors and uniform <= max_uniform, failures)
    return path


def main() -> int:
    failures = []
    shots = []
    print(f"writing to {SCREENSHOT_DIR}")

    h = Harness().title().step(3)
    shots.append(capture(h, "01-title", failures, min_colors=3))
    h.close()

    # Each level, from its spawn point.
    for index, level in enumerate(LEVELS):
        h = Harness().game()
        h.view._load_level(index)
        h.step(12)
        shots.append(capture(h, f"02-level{index + 1}-{level.name.lower().replace(' ', '-')}",
                             failures))
        if index == 0:
            # The world must animate (emitter telegraphs, fireballs, bob).
            before = h.image().tobytes()
            h.view.on_key_press(arcade.key.W, 0)
            h.step(30)
            h.view.on_key_release(arcade.key.W, 0)
            after = h.image().tobytes()
            check("level 1: walking forward changes the view", before != after, failures)
            shots.append(capture(h, "03-level1-after-walking", failures))

            h.view.minimap_on = True
            h.step(3)
            shots.append(capture(h, "04-minimap", failures))
            h.view.minimap_on = False

            # Hit flash + reduced hearts.
            h.view.health = 1
            h.view.flash = 0.4
            h.step(1)
            shots.append(capture(h, "05-hit-flash-one-heart", failures))

            # Death screen.
            # Past the 0.5s gate, so the retry hint is on screen too.
            h.view.player.alive = False
            h.step(45)
            shots.append(capture(h, "06-death", failures))

            # Win screen.
            h.view.player.alive = True
            h.view.won = True
            h.step(45)
            shots.append(capture(h, "07-win", failures))
            h.view.won = False

            # ESC hold bar, drawn over gameplay.
            h.hold(arcade.key.ESCAPE, 25)
            shots.append(capture(h, "08-esc-hold-bar", failures))
            h.release(arcade.key.ESCAPE)
        h.close()

    print(f"\n{len(shots)} screenshots in tests/screenshots/ -- open them and look")
    return report(failures, "screens")


if __name__ == "__main__":
    sys.exit(main())
