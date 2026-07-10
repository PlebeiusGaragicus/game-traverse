"""Fireballs, emitters, and portal."""

from __future__ import annotations

from typing import Callable

from src.config import FIREBALL_SPEED, FIREBALL_RADIUS, EMITTER_COOLDOWN, TELEGRAPH_SECONDS
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
        if cell >= 1 and cell not in (Tile.BRIDGE, Tile.CHASM, Tile.DOOR):
            self.alive = False

    def hits_player(self, px: float, py: float) -> bool:
        dx = self.x - px
        dy = self.y - py
        return dx * dx + dy * dy < FIREBALL_RADIUS * FIREBALL_RADIUS


class Emitter:
    __slots__ = ("gx", "gy", "dir_x", "dir_y", "period", "timer")

    def __init__(
        self,
        gx: int,
        gy: int,
        dir_x: int,
        dir_y: int,
        period: float = EMITTER_COOLDOWN,
        first_delay: float | None = None,
    ):
        self.gx = gx
        self.gy = gy
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.period = period
        if first_delay is None:
            first_delay = period * 0.5
        self.timer = period - first_delay

    @property
    def telegraphing(self) -> bool:
        """True while the emitter glows to warn of an imminent shot."""
        return self.timer >= self.period - TELEGRAPH_SECONDS

    def update(self, dt: float) -> Fireball | None:
        self.timer += dt
        if self.timer >= self.period:
            self.timer -= self.period
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
        emitter_timing: dict[tuple[int, int], tuple[float, float]] | None = None,
    ):
        timing = emitter_timing or {}
        self.emitters = [
            Emitter(gx, gy, dx, dy, *timing.get((gx, gy), (EMITTER_COOLDOWN, None)))
            for gx, gy, dx, dy in emitter_data
        ]
        self.fireballs: list[Fireball] = []
        self.portal = Portal(portal_x, portal_y)
        # Called with the new fireball on spawn (used for positional audio).
        self.on_spawn: Callable[[Fireball], None] | None = None

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
                if self.on_spawn is not None:
                    self.on_spawn(fb)
            # Swap the wall tile so the renderer shows the telegraph glow.
            world_map[emitter.gy][emitter.gx] = (
                Tile.EMITTER_HOT if emitter.telegraphing else Tile.EMITTER
            )

        hit = False
        for fb in self.fireballs:
            fb.update(dt, world_map, map_w, map_h)
            if fb.alive and fb.hits_player(player_x, player_y):
                hit = True
                fb.alive = False

        self.fireballs = [fb for fb in self.fireballs if fb.alive]

        portal_touch = self.portal.touches_player(player_x, player_y)

        return hit, portal_touch
