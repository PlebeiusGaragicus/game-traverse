"""Level data validation: run with `python tests/test_levels.py`.

Checks every level for rectangular grids, reachable portals and triggers,
walkable spawn/teleport destinations, and sane emitter definitions.
"""

import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.map_data import LEVELS, Tile, WALKABLE, find_emitters


def bfs_reachable(grid, sources):
    h, w = len(grid), len(grid[0])
    seen = set()
    queue = deque()
    for gx, gy in sources:
        if (gx, gy) not in seen:
            seen.add((gx, gy))
            queue.append((gx, gy))
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen:
                if grid[ny][nx] in WALKABLE:
                    seen.add((nx, ny))
                    queue.append((nx, ny))
    return seen


def check_level(index, level):
    grid = level.grid
    h, w = len(grid), len(grid[0])
    name = f"level {index + 1} ({level.name})"

    assert all(len(row) == w for row in grid), f"{name}: grid is not rectangular"

    sx, sy, _ = level.start
    assert grid[int(sy)][int(sx)] in WALKABLE, f"{name}: start tile not walkable"

    # Sources for reachability: the start plus every teleport destination.
    sources = [(int(sx), int(sy))]
    for (tx, ty), trig in level.triggers.items():
        assert grid[ty][tx] in WALKABLE, f"{name}: trigger tile ({tx},{ty}) not walkable"
        if trig["action"] == "teleport":
            dx, dy = int(trig["x"]), int(trig["y"])
            assert grid[dy][dx] in WALKABLE, f"{name}: teleport dest ({dx},{dy}) not walkable"
            assert trig["phase"] in level.phases, f"{name}: teleport to unknown phase"
            sources.append((dx, dy))
    assert level.start_phase in level.phases, f"{name}: unknown start phase"

    reachable = bfs_reachable(grid, sources)

    px, py = int(level.portal[0]), int(level.portal[1])
    assert grid[py][px] in WALKABLE, f"{name}: portal tile ({px},{py}) not walkable"
    assert (px, py) in reachable, f"{name}: portal not reachable"

    for (tx, ty) in level.triggers:
        assert (tx, ty) in reachable, f"{name}: trigger ({tx},{ty}) not reachable"

    # Every emitter tile must resolve to a firing direction.
    emitter_tiles = [
        (gx, gy) for gy in range(h) for gx in range(w) if grid[gy][gx] == Tile.EMITTER
    ]
    emitters = find_emitters(grid, level.emitter_dirs)
    assert len(emitters) == len(emitter_tiles), (
        f"{name}: {len(emitter_tiles)} emitter tiles but only "
        f"{len(emitters)} resolved a direction"
    )
    assert len(emitter_tiles) > 0, f"{name}: no emitters"

    # Timing/direction overrides must point at actual emitter tiles.
    for key in level.emitter_timing:
        assert key in emitter_tiles, f"{name}: emitter_timing for non-emitter {key}"
    for key in level.emitter_dirs:
        assert key in emitter_tiles, f"{name}: emitter_dirs for non-emitter {key}"

    # Each emitter's first fireball step must not start inside a wall.
    for gx, gy, dx, dy in emitters:
        nx, ny = gx + dx, gy + dy
        assert 0 <= nx < w and 0 <= ny < h, f"{name}: emitter ({gx},{gy}) fires off-map"
        cell = grid[ny][nx]
        assert cell in (Tile.EMPTY, Tile.DOOR, Tile.BRIDGE, Tile.CHASM), (
            f"{name}: emitter ({gx},{gy}) fires into a wall"
        )

    print(f"{name}: OK ({len(reachable)} reachable tiles, {len(emitters)} emitters)")


def main():
    assert len(LEVELS) >= 3
    for i, level in enumerate(LEVELS):
        check_level(i, level)
    print("all level checks passed")


if __name__ == "__main__":
    main()
