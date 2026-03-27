"""Procedurally generated 64x64 wall textures stored as flat RGBA bytearrays."""

import random

from src.config import TEX_SIZE

_RNG = random.Random(42)

TEX_BYTES = TEX_SIZE * TEX_SIZE * 4  # RGBA


def _make_buffer() -> bytearray:
    return bytearray(TEX_BYTES)


def _set_pixel(buf: bytearray, x: int, y: int, r: int, g: int, b: int, a: int = 255):
    idx = (y * TEX_SIZE + x) * 4
    buf[idx] = r
    buf[idx + 1] = g
    buf[idx + 2] = b
    buf[idx + 3] = a


def _get_pixel(buf: bytearray, x: int, y: int) -> tuple[int, int, int, int]:
    idx = (y * TEX_SIZE + x) * 4
    return buf[idx], buf[idx + 1], buf[idx + 2], buf[idx + 3]


def _clamp(v: int) -> int:
    return max(0, min(255, v))


def generate_stone() -> bytearray:
    """Gray stone with noise and mortar lines."""
    buf = _make_buffer()
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            base = 100 + _RNG.randint(-15, 15)
            is_mortar = (y % 16 < 2) or (x % 16 < 2 and (y // 16) % 2 == 0)
            if is_mortar:
                base = 60 + _RNG.randint(-5, 5)
            _set_pixel(buf, x, y, _clamp(base), _clamp(base - 5), _clamp(base - 10))
    return buf


def generate_brick() -> bytearray:
    """Red/brown brick pattern."""
    buf = _make_buffer()
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            row = y // 8
            offset = 16 if row % 2 else 0
            mx = (x + offset) % 32
            is_mortar = (y % 8 < 1) or (mx < 1)
            if is_mortar:
                g = 80 + _RNG.randint(-5, 5)
                _set_pixel(buf, x, y, g, g - 10, g - 15)
            else:
                r = 140 + _RNG.randint(-20, 20)
                _set_pixel(buf, x, y, _clamp(r), _clamp(r // 2 - 10), _clamp(r // 3 - 10))
    return buf


def generate_metal() -> bytearray:
    """Dark gray metal with vertical streaks."""
    buf = _make_buffer()
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            base = 55 + _RNG.randint(-8, 8)
            if x % 16 == 0 or x % 16 == 15:
                base += 25
            if y % 32 < 2:
                base += 15
            _set_pixel(buf, x, y, _clamp(base), _clamp(base), _clamp(base + 5))
    return buf


def generate_lava_rock() -> bytearray:
    """Dark rock with orange/red veins."""
    buf = _make_buffer()
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            base = 30 + _RNG.randint(-10, 10)
            vein = ((x * 7 + y * 13) % 37) < 3 or ((x * 11 + y * 5) % 29) < 2
            if vein:
                r = 200 + _RNG.randint(-30, 30)
                g = 80 + _RNG.randint(-20, 20)
                _set_pixel(buf, x, y, _clamp(r), _clamp(g), 10)
            else:
                _set_pixel(buf, x, y, _clamp(base), _clamp(base - 5), _clamp(base - 8))
    return buf


def generate_door() -> bytearray:
    """Wooden door -- brown with planks and a handle."""
    buf = _make_buffer()
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            base_r = 100 + _RNG.randint(-10, 10)
            base_g = 60 + _RNG.randint(-8, 8)
            base_b = 30 + _RNG.randint(-5, 5)
            if x % 16 < 1:
                base_r -= 20
                base_g -= 15
                base_b -= 10
            _set_pixel(buf, x, y, _clamp(base_r), _clamp(base_g), _clamp(base_b))
    # door handle
    for dy in range(28, 36):
        for dx in range(48, 54):
            if 0 <= dx < TEX_SIZE and 0 <= dy < TEX_SIZE:
                _set_pixel(buf, dx, dy, 200, 180, 50)
    return buf


def generate_emitter() -> bytearray:
    """Dark wall with a glowing orange emitter hole in the center."""
    buf = generate_metal()
    cx, cy = TEX_SIZE // 2, TEX_SIZE // 2
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            dx = x - cx
            dy = y - cy
            dist_sq = dx * dx + dy * dy
            if dist_sq < 64:
                t = dist_sq / 64
                r = int(255 * (1 - t) + 100 * t)
                g = int(140 * (1 - t) + 40 * t)
                _set_pixel(buf, x, y, _clamp(r), _clamp(g), 10)
    return buf


def generate_fireball_sprite() -> bytearray:
    """32x32 radial gradient fireball, stored as 32x32 RGBA."""
    size = 32
    buf = bytearray(size * size * 4)
    cx, cy = size // 2, size // 2
    max_r = size // 2
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > max_r:
                idx = (y * size + x) * 4
                buf[idx] = 0
                buf[idx + 1] = 0
                buf[idx + 2] = 0
                buf[idx + 3] = 0
            else:
                t = dist / max_r
                r = int(255 * (1 - t * 0.3))
                g = int(200 * (1 - t * 0.7))
                b = int(50 * (1 - t))
                a = int(255 * (1 - t * t))
                idx = (y * size + x) * 4
                buf[idx] = _clamp(r)
                buf[idx + 1] = _clamp(g)
                buf[idx + 2] = _clamp(b)
                buf[idx + 3] = _clamp(a)
    return buf


def generate_portal_sprite() -> bytearray:
    """32x32 blue/cyan swirling portal."""
    size = 32
    buf = bytearray(size * size * 4)
    cx, cy = size // 2, size // 2
    max_r = size // 2
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > max_r:
                idx = (y * size + x) * 4
                buf[idx] = 0
                buf[idx + 1] = 0
                buf[idx + 2] = 0
                buf[idx + 3] = 0
            else:
                t = dist / max_r
                swirl = ((x * 3 + y * 7) % 13) / 13
                r = int(30 * swirl)
                g = int(150 * (1 - t) + 80 * t)
                b = int(255 * (1 - t * 0.5))
                a = int(220 * (1 - t * t))
                idx = (y * size + x) * 4
                buf[idx] = _clamp(r)
                buf[idx + 1] = _clamp(g)
                buf[idx + 2] = _clamp(b)
                buf[idx + 3] = _clamp(a)
    return buf


class TextureAtlas:
    """Holds all generated textures, indexed by tile ID."""

    def __init__(self):
        self.wall_textures: dict[int, bytearray] = {
            1: generate_stone(),
            2: generate_brick(),
            3: generate_metal(),
            4: generate_lava_rock(),
            5: generate_door(),
            7: generate_emitter(),
        }
        self.fireball_sprite = generate_fireball_sprite()
        self.portal_sprite = generate_portal_sprite()
        self.fireball_size = 32
        self.portal_size = 32

    def get_wall(self, tile_id: int) -> bytearray | None:
        return self.wall_textures.get(tile_id)

    def sample_wall(self, tile_id: int, tex_x: int, tex_y: int) -> tuple[int, int, int, int]:
        tex = self.wall_textures.get(tile_id)
        if tex is None:
            return (128, 0, 128, 255)
        tx = tex_x & (TEX_SIZE - 1)
        ty = tex_y & (TEX_SIZE - 1)
        idx = (ty * TEX_SIZE + tx) * 4
        return tex[idx], tex[idx + 1], tex[idx + 2], tex[idx + 3]
