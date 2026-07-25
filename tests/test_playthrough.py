"""Simulated play: run with `.venv/bin/python tests/test_playthrough.py`.

Drives the real GameView and asserts invariants that must hold whatever the
player does. Correctness only -- whether the maze is fun or fair is a human
question.
"""

import random
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from harness import Harness, check, report  # noqa: E402

import arcade  # noqa: E402

from src.config import MAX_HEALTH  # noqa: E402
from src.map_data import LEVELS, WALKABLE  # noqa: E402

MOVE_KEYS = [arcade.key.W, arcade.key.S, arcade.key.A, arcade.key.D,
             arcade.key.LEFT, arcade.key.RIGHT]
FRAMES = 900  # 15s at 60fps


def in_walkable_tile(view) -> bool:
    gx, gy = int(view.player.x), int(view.player.y)
    if not (0 <= gy < view.map_h and 0 <= gx < view.map_w):
        return False
    return view.grid[gy][gx] in WALKABLE


def check_random_input_playthrough(failures):
    """Mash the controls; the player must never end up inside a wall."""
    rng = random.Random(7)
    h = Harness().game()
    v = h.view

    held = set()
    inside_wall = 0
    min_health, max_health_seen = MAX_HEALTH, 0

    for _ in range(FRAMES):
        if rng.random() < 0.25:
            key = rng.choice(MOVE_KEYS)
            if key in held:
                v.on_key_release(key, 0)
                held.discard(key)
            else:
                v.on_key_press(key, 0)
                held.add(key)
        h.step(1)

        if not v.player.alive or v.won:
            break
        if not in_walkable_tile(v):
            inside_wall += 1
        min_health = min(min_health, v.health)
        max_health_seen = max(max_health_seen, v.health)

    check(f"survived {h.frames} frames of random input without crashing", True, failures)
    check("player never ended up inside a wall", inside_wall == 0, failures)
    check(f"health stayed in [0, {MAX_HEALTH}] (low {min_health})",
          0 <= min_health and max_health_seen <= MAX_HEALTH, failures)
    check("player coordinates stayed finite",
          all(abs(c) < 1e6 for c in (v.player.x, v.player.y)), failures)
    h.close()


def check_walls_block_movement(failures):
    """Walk face-first into a wall for 2s; the player must not pass through."""
    h = Harness().game()
    v = h.view

    # Point at the nearest wall by scanning angles for the shortest clear run.
    import math

    best_angle, best_dist = 0.0, 1e9
    for i in range(32):
        angle = i * math.tau / 32
        dist = 0.0
        while dist < 8:
            dist += 0.1
            gx = int(v.player.x + math.cos(angle) * dist)
            gy = int(v.player.y + math.sin(angle) * dist)
            if not (0 <= gy < v.map_h and 0 <= gx < v.map_w) or v.grid[gy][gx] not in WALKABLE:
                break
        if dist < best_dist:
            best_angle, best_dist = angle, dist

    v.player.angle = best_angle
    v.on_key_press(arcade.key.W, 0)
    h.step(120)
    v.on_key_release(arcade.key.W, 0)

    check(f"walked into a wall {best_dist:.1f} units away and stayed walkable",
          in_walkable_tile(v), failures)
    h.close()


def check_death_and_respawn(failures):
    """Death via the real path: a fireball hit that takes the last heart."""
    h = Harness().game()
    v = h.view
    v.health = 1
    v.iframes = 0.0

    # Put a fireball on top of the player so entities.update reports a hit.
    from src.entities import Fireball

    v.entities.fireballs.append(Fireball(v.player.x, v.player.y, 0.0, 0.0))
    h.step(3)

    check("a hit that takes the last heart kills the player",
          not v.player.alive, failures)
    check("health reached zero", v.health <= 0, failures)

    h.step(60)  # past the 0.5s input lockout on the death screen
    v.on_key_press(arcade.key.SPACE, 0)
    h.step(5)
    check("a key press after death respawns", v.player.alive, failures)
    check("respawn restores health", v.health == MAX_HEALTH, failures)
    h.close()


def check_all_levels_load_and_render(failures):
    """Every level must build and draw -- not just level 1."""
    for index in range(len(LEVELS)):
        h = Harness().game()
        h.view._load_level(index)
        h.step(10)
        v = h.view
        check(f"level {index + 1} ({LEVELS[index].name}) loads and the player spawns walkable",
              v.level_index == index and in_walkable_tile(v), failures)
        h.close()


def check_esc_hold_quits(failures):
    h = Harness().game()
    closed = []
    h.window.close = lambda: closed.append(True)

    h.hold(arcade.key.ESCAPE, 20, dt=1 / 60)  # ~0.33s
    check("still running mid-hold", not closed, failures)
    h.step(50, dt=1 / 60)  # past 1s total
    check("ESC held past the threshold closes the window", len(closed) >= 1, failures)
    h.view.on_key_release(arcade.key.ESCAPE, 0)
    h.window.close = lambda: None
    h.close()


def main() -> int:
    failures = []
    print("random-input playthrough")
    check_random_input_playthrough(failures)
    print("\ncollision")
    check_walls_block_movement(failures)
    print("\ndeath / respawn")
    check_death_and_respawn(failures)
    print("\nlevels")
    check_all_levels_load_and_render(failures)
    print("\nESC protocol")
    check_esc_hold_quits(failures)
    return report(failures, "playthrough")


if __name__ == "__main__":
    sys.exit(main())
