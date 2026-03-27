"""Player state: position, angle, movement with wall collision and sliding."""

from __future__ import annotations

import math

from src.config import MOVE_SPEED, STRAFE_SPEED, TURN_SPEED, PLAYER_RADIUS


class Player:
    def __init__(self, x: float, y: float, angle: float = 0.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.alive = True
        self.won = False

    def update(
        self,
        dt: float,
        move_fwd: bool,
        move_back: bool,
        strafe_left: bool,
        strafe_right: bool,
        turn_left: bool,
        turn_right: bool,
        world_map: list[list[int]],
        map_w: int,
        map_h: int,
    ):
        if not self.alive:
            return

        if turn_left:
            self.angle -= TURN_SPEED * dt
        if turn_right:
            self.angle += TURN_SPEED * dt

        dx = 0.0
        dy = 0.0
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        if move_fwd:
            dx += cos_a * MOVE_SPEED * dt
            dy += sin_a * MOVE_SPEED * dt
        if move_back:
            dx -= cos_a * MOVE_SPEED * dt
            dy -= sin_a * MOVE_SPEED * dt
        if strafe_left:
            dx += sin_a * STRAFE_SPEED * dt
            dy -= cos_a * STRAFE_SPEED * dt
        if strafe_right:
            dx -= sin_a * STRAFE_SPEED * dt
            dy += cos_a * STRAFE_SPEED * dt

        if dx == 0.0 and dy == 0.0:
            return

        self._try_move(dx, dy, world_map, map_w, map_h)

    def _is_solid(self, gx: int, gy: int, world_map: list[list[int]], map_w: int, map_h: int) -> bool:
        if gx < 0 or gx >= map_w or gy < 0 or gy >= map_h:
            return True
        cell = world_map[gy][gx]
        # 0=empty, 5=door(walkable trigger), 6=bridge, 8=chasm
        return cell >= 1 and cell not in (5, 6, 8)

    def _is_deadly(self, gx: int, gy: int, world_map: list[list[int]], map_w: int, map_h: int) -> bool:
        if gx < 0 or gx >= map_w or gy < 0 or gy >= map_h:
            return False
        return world_map[gy][gx] == 8

    def _try_move(
        self,
        dx: float,
        dy: float,
        world_map: list[list[int]],
        map_w: int,
        map_h: int,
    ):
        r = PLAYER_RADIUS
        new_x = self.x + dx
        new_y = self.y + dy

        # Check deadly tiles (chasm)
        gx = int(new_x)
        gy = int(new_y)
        if self._is_deadly(gx, gy, world_map, map_w, map_h):
            self.alive = False
            return

        # Wall sliding: try full move, then each axis independently
        if not self._collides(new_x, new_y, r, world_map, map_w, map_h):
            self.x = new_x
            self.y = new_y
        elif not self._collides(new_x, self.y, r, world_map, map_w, map_h):
            self.x = new_x
        elif not self._collides(self.x, new_y, r, world_map, map_w, map_h):
            self.y = new_y

        # Check if standing on door tile
        gx = int(self.x)
        gy = int(self.y)
        if 0 <= gx < map_w and 0 <= gy < map_h:
            if world_map[gy][gx] == 5:
                self.won = True

    def _collides(
        self,
        cx: float,
        cy: float,
        r: float,
        world_map: list[list[int]],
        map_w: int,
        map_h: int,
    ) -> bool:
        """Check if a circle at (cx, cy) with radius r overlaps any solid cell."""
        min_gx = int(cx - r)
        max_gx = int(cx + r)
        min_gy = int(cy - r)
        max_gy = int(cy + r)

        for gy in range(min_gy, max_gy + 1):
            for gx in range(min_gx, max_gx + 1):
                if self._is_solid(gx, gy, world_map, map_w, map_h):
                    nearest_x = max(gx, min(gx + 1.0, cx))
                    nearest_y = max(gy, min(gy + 1.0, cy))
                    dist_x = cx - nearest_x
                    dist_y = cy - nearest_y
                    if dist_x * dist_x + dist_y * dist_y < r * r:
                        return True
        return False
