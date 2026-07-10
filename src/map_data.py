"""Level data: tile types, level definitions, and emitter discovery.

Tile legend:
  0 = empty (walkable, stone floor)
  1 = stone wall
  2 = brick wall
  3 = metal wall
  4 = lava rock wall
  5 = door (walkable)
  6 = bridge floor (walkable, chasm visual below)
  7 = emitter wall (spawns fireballs)
  8 = chasm (instant death)
  9 = emitter wall, telegraphing (runtime-only: emitters swap 7<->9)

A Level is pure data. Door tiles are inert by themselves; `triggers` maps
tile coordinates to actions (currently "teleport", which also sets the
respawn checkpoint). Touching the level's portal advances to the next level
(or wins the game on the last one). Emitters are discovered from the grid;
`emitter_dirs` overrides the auto-detected fire direction and
`emitter_timing` sets (period, first_delay) per emitter.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntEnum


class Tile(IntEnum):
    EMPTY = 0
    STONE = 1
    BRICK = 2
    METAL = 3
    LAVA = 4
    DOOR = 5
    BRIDGE = 6
    EMITTER = 7
    CHASM = 8
    EMITTER_HOT = 9


WALKABLE = (Tile.EMPTY, Tile.DOOR, Tile.BRIDGE)


@dataclass(frozen=True)
class Phase:
    label: str                            # HUD label, e.g. "THE MAZE"
    ceiling: tuple[int, int, int, int]
    floor: tuple[int, int, int, int]
    floor_cast: bool                      # per-pixel floor casting vs solid fill


@dataclass(frozen=True)
class Level:
    name: str
    grid: list[list[int]]                 # template; deep-copied when loaded
    start: tuple[float, float, float]     # x, y, angle
    start_phase: str
    phases: dict[str, Phase]
    triggers: dict[tuple[int, int], dict]
    portal: tuple[float, float]
    emitter_dirs: dict[tuple[int, int], tuple[int, int]] = field(default_factory=dict)
    emitter_timing: dict[tuple[int, int], tuple[float, float]] = field(default_factory=dict)


_ = Tile.EMPTY
S = Tile.STONE
B = Tile.BRICK
M = Tile.METAL
L = Tile.LAVA
D = Tile.DOOR
R = Tile.BRIDGE  # bRidge
E = Tile.EMITTER
C = Tile.CHASM

# fmt: off
_MAZE_GRID = [
    #  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29
    [  S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S],  # 0
    [  S, _, _, _, S, _, _, _, _, _, _, _, S, _, _, _, _, _, S, _, _, _, _, _, _, _, _, _, _, S],  # 1
    [  S, _, S, _, S, _, S, S, S, _, S, _, S, _, S, S, S, _, S, _, S, S, S, S, S, _, S, S, _, S],  # 2
    [  S, _, S, _, _, _, _, _, S, _, S, _, _, _, S, _, _, _, _, _, _, _, _, _, S, _, _, S, _, S],  # 3
    [  S, _, S, S, S, S, S, _, S, _, S, S, S, S, S, _, S, S, S, S, S, S, S, _, _, S, _, _, _, S],  # 4
    [  S, _, _, _, _, _, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, S, _, S, S, _, S, _, S],  # 5
    [  S, S, S, _, S, _, S, S, S, S, S, _, S, S, S, S, S, S, _, S, _, _, S, _, _, _, _, S, _, S],  # 6
    [  S, _, _, _, S, _, _, _, _, _, S, _, _, _, _, _, _, S, _, S, _, S, S, S, S, S, _, S, _, S],  # 7
    [  S, _, S, S, S, S, S, S, S, _, S, _, S, S, S, S, _, _, _, S, _, _, _, _, _, S, _, _, _, S],  # 8
    [  S, _, _, _, _, _, _, _, S, _, S, _, S, _, _, S, _, S, S, S, _, S, S, S, _, S, _, S, _, S],  # 9
    [  S, _, S, S, S, _, S, _, _, _, _, _, S, _, _, _, _, _, _, _, _, _, _, S, _, _, _, S, _, S],  # 10
    [  S, _, _, _, S, _, S, S, S, S, S, S, S, S, S, _, S, S, S, S, S, S, _, S, S, S, S, S, _, S],  # 11
    [  S, S, S, _, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, S, _, _, _, _, _, _, _, S],  # 12
    [  S, _, _, _, S, _, S, S, S, S, S, S, S, S, S, S, S, S, S, _, S, S, S, _, S, S, S, S, _, S],  # 13
    [  S, _, S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, S, _, _, _, _, _, _, _, _, S, _, S],  # 14
    [  S, _, S, S, S, S, S, S, S, _, S, S, S, S, S, S, S, _, S, _, S, S, S, S, S, S, _, _, _, S],  # 15
    [  S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, S, _, _, _, _, _, _, _, _, S, _, S, _, S],  # 16
    [  S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, _, S, S, S, S, S, S, S, S, _, S, _, S],  # 17
    [  S, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, S],  # 18
    [  S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, S, D, S, S],  # 19
    # --- bridge section below ---
    [  L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, _, L, L],  # 20
    [  L, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, E, R, C, L],  # 21
    [  L, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, R, C, L],  # 22
    [  L, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, E, C, C, C, R, C, L],  # 23
    [  L, C, C, E, C, C, C, C, C, C, E, C, C, C, C, C, C, E, C, C, C, C, C, C, C, C, C, R, C, L],  # 24
    [  L, C, C, C, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, C, L],  # 25
    [  L, C, C, C, R, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, L],  # 26
    [  L, C, E, C, R, C, C, C, C, E, C, C, C, C, C, E, C, C, C, C, C, C, E, C, C, C, C, C, C, L],  # 27
    [  L, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, R, C, C, C, C, C, L],  # 28
    [  L, R, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, L],  # 29
    [  L, R, C, C, C, C, C, C, C, C, E, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, L],  # 30
    [  L, R, C, E, C, C, C, C, C, C, C, C, C, C, C, C, C, E, C, C, C, C, C, C, C, C, C, C, C, L],  # 31
    [  L, D, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, C, L],  # 32
    [  L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L, L],  # 33
]
# fmt: on


def _build_gauntlet() -> list[list[int]]:
    """Serpentine brick corridors; an emitter fires along each one."""
    w, h = 23, 15
    g = [[B] * w for _ in range(h)]
    for row in (1, 4, 7, 10, 13):
        for x in range(1, 22):
            g[row][x] = _
    # Connectors between corridors, alternating east/west ends
    for y in (2, 3):
        g[y][21] = _
    for y in (5, 6):
        g[y][1] = _
    for y in (8, 9):
        g[y][21] = _
    for y in (11, 12):
        g[y][1] = _
    # Dodge alcoves cut into the corridor walls
    for x, y in [(5, 2), (11, 2), (16, 2), (7, 5), (13, 5), (18, 5),
                 (4, 8), (9, 8), (14, 8), (6, 11), (12, 11), (17, 11)]:
        g[y][x] = _
    # Emitters at corridor ends: odd corridors chase from the west,
    # even corridors fire into the player's face from the east.
    g[1][0] = E
    g[4][22] = E
    g[7][0] = E
    g[10][22] = E
    g[13][0] = E
    return g


def _build_crossing() -> list[list[int]]:
    """Open chasm with branching bridges and emitter pillars."""
    w, h = 30, 20
    g = [[C] * w for _ in range(h)]
    for x in range(w):
        g[0][x] = L
        g[h - 1][x] = L
    for y in range(h):
        g[y][0] = L
        g[y][w - 1] = L
    # Start platform (west) and portal platform (east)
    for y in (8, 9, 10):
        for x in (1, 2, 3):
            g[y][x] = _
        for x in (27, 28):
            g[y][x] = _
    # Main bridge along row 9
    for x in range(4, 27):
        g[9][x] = R
    # North detour: fewer emitters but longer
    for y in range(5, 9):
        g[y][6] = R
        g[y][23] = R
    for x in range(6, 24):
        g[4][x] = R
    # Short dead-end branch south from the main bridge
    for y in range(10, 13):
        g[y][10] = R
    # Emitter pillars in the chasm, aimed across the bridges
    g[11][12] = E
    g[7][18] = E
    g[6][8] = E
    g[2][15] = E
    # Border emitters firing down the long straights
    g[9][0] = E
    g[4][29] = E
    return g


LEVELS: list[Level] = [
    Level(
        name="The Maze",
        grid=_MAZE_GRID,
        start=(1.5, 1.5, 0.0),
        start_phase="maze",
        phases={
            "maze": Phase("THE MAZE", (60, 60, 70, 255), (90, 85, 80, 255), False),
            "bridge": Phase("THE BRIDGE", (20, 10, 10, 255), (15, 10, 8, 255), True),
        },
        triggers={
            # Maze exit door: drop onto the bridge entrance, facing south.
            (27, 19): {
                "action": "teleport",
                "x": 27.5, "y": 20.5, "angle": math.pi / 2,
                "phase": "bridge",
            },
        },
        portal=(1.5, 32.5),
    ),
    Level(
        name="The Gauntlet",
        grid=_build_gauntlet(),
        start=(1.5, 1.5, 0.0),
        start_phase="gauntlet",
        phases={
            "gauntlet": Phase("THE GAUNTLET", (52, 42, 42, 255), (72, 62, 56, 255), False),
        },
        triggers={},
        portal=(21.5, 13.5),
        emitter_timing={
            (0, 1): (3.2, 2.5),    # chaser behind the start: late first shot
            (22, 4): (2.8, 1.2),
            (0, 7): (3.0, 1.5),
            (22, 10): (2.6, 0.8),
            (0, 13): (2.4, 1.0),   # final sprint to the portal
        },
    ),
    Level(
        name="The Crossing",
        grid=_build_crossing(),
        start=(2.0, 9.5, 0.0),
        start_phase="crossing",
        phases={
            "crossing": Phase("THE CROSSING", (18, 8, 8, 255), (15, 10, 8, 255), True),
        },
        triggers={},
        portal=(27.5, 9.5),
        emitter_dirs={
            # Chasm pillars: auto-detection can't know which way the bridge is.
            (12, 11): (0, -1),
            (18, 7): (0, 1),
            (8, 6): (-1, 0),
            (15, 2): (0, 1),
        },
        emitter_timing={
            (0, 9): (4.0, 3.0),    # long chaser down the main bridge
            (29, 4): (4.0, 2.0),   # long chaser down the north route
            (15, 2): (3.0, 1.0),
            (12, 11): (2.5, 0.5),
            (18, 7): (2.5, 1.75),
            (8, 6): (3.0, 1.5),
        },
    ),
]


def find_emitters(
    level: list[list[int]],
    dir_overrides: dict[tuple[int, int], tuple[int, int]] | None = None,
) -> list[tuple[int, int, int, int]]:
    """Find emitter walls and determine their fire direction.

    Returns list of (grid_x, grid_y, dir_x, dir_y). Direction is toward the
    first adjacent empty/bridge/chasm tile unless overridden.
    """
    dir_overrides = dir_overrides or {}
    h = len(level)
    w = len(level[0])
    emitters = []
    for gy in range(h):
        for gx in range(w):
            if level[gy][gx] != Tile.EMITTER:
                continue
            override = dir_overrides.get((gx, gy))
            if override is not None:
                emitters.append((gx, gy, override[0], override[1]))
                continue
            for ddx, ddy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = gx + ddx, gy + ddy
                if 0 <= nx < w and 0 <= ny < h:
                    cell = level[ny][nx]
                    if cell in (Tile.EMPTY, Tile.BRIDGE, Tile.CHASM):
                        emitters.append((gx, gy, ddx, ddy))
                        break
    return emitters
