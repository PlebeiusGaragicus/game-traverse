"""Fireballs, emitters, and portal."""

from __future__ import annotations

import math

from src.config import FIREBALL_SPEED, FIREBALL_RADIUS, EMITTER_COOLDOWN
from src.map_data import Tile


class Fireball:
    __slots__ = ("x", "y", "dx", "dy", "alive")

    def __init__(self, x: float, y: float, dx: float, dy: float):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.alive = True

    def update(self, dt: float, world_map: list[list[int]], map_w: int, map_h: int):
        self.x += self.dx * FIREBALL_SPEED * dt
        self.y += self.dy * FIREBALL_SPEED * dt

        gx = int(self.x)
        gy = int(self.y)
        if gx < 0 or gx >= map_w or gy < 0 or gy >= map_h:
            self.alive = False
            return

        cell = world_map[gy][gx]
        if cell >= 1 and cell not in (Tile.EMPTY, Tile.BRIDGE, Tile.CHASM, Tile.DOOR):
            self.alive = False

    def hits_player(self, px: float, py: float) -> bool:
        dx = self.x - px
        dy = self.y - py
        return dx * dx + dy * dy < FIREBALL_RADIUS * FIREBALL_RADIUS


class Emitter:
    __slots__ = ("gx", "gy", "dir_x", "dir_y", "cooldown", "timer")

    def __init__(self, gx: int, gy: int, dir_x: int, dir_y: int):
        self.gx = gx
        self.gy = gy
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.cooldown = EMITTER_COOLDOWN
        self.timer = EMITTER_COOLDOWN * 0.5  # stagger initial spawn

    def update(self, dt: float) -> Fireball | None:
        self.timer += dt
        if self.timer >= self.cooldown:
            self.timer -= self.cooldown
            spawn_x = self.gx + 0.5 + self.dir_x * 0.6
            spawn_y = self.gy + 0.5 + self.dir_y * 0.6
            return Fireball(spawn_x, spawn_y, float(self.dir_x), float(self.dir_y))
        return None


class Portal:
    __slots__ = ("x", "y", "radius")

    def __init__(self, x: float, y: float, radius: float = 0.5):
        self.x = x
        self.y = y
        self.radius = radius

    def touches_player(self, px: float, py: float) -> bool:
        dx = self.x - px
        dy = self.y - py
        return dx * dx + dy * dy < self.radius * self.radius


class EntityManager:
    """Manages all fireballs, emitters, and the portal."""

    def __init__(
        self,
        emitter_data: list[tuple[int, int, int, int]],
        portal_x: float,
        portal_y: float,
    ):
        self.emitters = [Emitter(gx, gy, dx, dy) for gx, gy, dx, dy in emitter_data]
        self.fireballs: list[Fireball] = []
        self.portal = Portal(portal_x, portal_y)

    def update(
        self,
        dt: float,
        world_map: list[list[int]],
        map_w: int,
        map_h: int,
        player_x: float,
        player_y: float,
    ) -> tuple[bool, bool]:
        """Update all entities. Returns (player_hit_by_fireball, player_reached_portal)."""
        for emitter in self.emitters:
            fb = emitter.update(dt)
            if fb is not None:
                self.fireballs.append(fb)

        hit = False
        for fb in self.fireballs:
            fb.update(dt, world_map, map_w, map_h)
            if fb.alive and fb.hits_player(player_x, player_y):
                hit = True

        self.fireballs = [fb for fb in self.fireballs if fb.alive]

        portal_touch = self.portal.touches_player(player_x, player_y)

        return hit, portal_touch
