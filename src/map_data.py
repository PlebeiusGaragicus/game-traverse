"""Level map data and tile types.

Tile legend:
  0 = empty (walkable)
  1 = stone wall
  2 = brick wall
  3 = metal wall
  4 = lava rock wall
  5 = door / exit trigger (walkable)
  6 = bridge floor (walkable, chasm visual below)
  7 = emitter wall (spawns fireballs)
  8 = chasm (instant death)
"""

from __future__ import annotations

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
LEVEL_1 = [
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

LEVEL_1_WIDTH = len(LEVEL_1[0])
LEVEL_1_HEIGHT = len(LEVEL_1)

# Player start: inside the maze, top-left area
PLAYER_START_X = 1.5
PLAYER_START_Y = 1.5
PLAYER_START_ANGLE = 0.0

# Portal position: at the end of the bridge (bottom-left)
PORTAL_X = 1.5
PORTAL_Y = 32.5

# Emitter positions are auto-discovered from the map
def find_emitters(level: list[list[int]]) -> list[tuple[int, int, int, int]]:
    """Find emitter walls and determine their fire direction.

    Returns list of (grid_x, grid_y, dir_x, dir_y) where dir is the
    direction fireballs should travel (perpendicular to wall, toward empty/bridge/chasm).
    """
    h = len(level)
    w = len(level[0])
    emitters = []
    for gy in range(h):
        for gx in range(w):
            if level[gy][gx] != Tile.EMITTER:
                continue
            for ddx, ddy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = gx + ddx, gy + ddy
                if 0 <= nx < w and 0 <= ny < h:
                    cell = level[ny][nx]
                    if cell in (Tile.EMPTY, Tile.BRIDGE, Tile.CHASM):
                        emitters.append((gx, gy, ddx, ddy))
                        break
    return emitters
