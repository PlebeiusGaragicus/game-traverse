"""NumPy framebuffer renderer: walls, floor casting, and billboarded sprites.

The framebuffer `fb` is a (RENDER_HEIGHT, RENDER_WIDTH, 4) uint8 array in
top-down row order: row 0 is the top of the screen. It is handed to pyglet
with a negative pitch, which tells GL the data is top-to-bottom, so no draw
code ever needs to flip Y.

Walls and sprites both use camera-plane projection with perpendicular
distance, so sprite positions and occlusion stay consistent with wall
geometry across the whole field of view.
"""

from __future__ import annotations

import math

import numpy as np
import pyglet
from pyglet.gl import GL_NEAREST, glTexParameteri, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER

from src.config import (
    RENDER_WIDTH, RENDER_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
    TEX_SIZE, HALF_FOV, COLOR_CEILING_MAZE, COLOR_FLOOR_MAZE,
    COLOR_BRIDGE_FLOOR_A, COLOR_BRIDGE_FLOOR_B,
    COLOR_CHASM_TILE, COLOR_STONE_FLOOR_TILE,
)
from src.map_data import Tile
from src.textures import TextureAtlas

# Base floor color per tile ID for the bridge-phase floor caster.
# Bridge (6) and chasm (8) get special handling; the rest use this LUT.
_FLOOR_LUT = np.full((9, 3), (30, 25, 20), dtype=np.float64)
_FLOOR_LUT[Tile.EMPTY] = COLOR_STONE_FLOOR_TILE
_FLOOR_LUT[Tile.DOOR] = COLOR_STONE_FLOOR_TILE
_FLOOR_LUT[Tile.CHASM] = COLOR_CHASM_TILE

_OUT_OF_BOUNDS_COLOR = (5, 2, 2)


class Renderer:
    def __init__(self, atlas: TextureAtlas):
        self.atlas = atlas
        self.width = RENDER_WIDTH
        self.height = RENDER_HEIGHT
        self.stride = self.width * 4

        self.fb = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        self.fb[..., 3] = 255
        self.depth = np.full(self.width, np.inf, dtype=np.float64)

        self.ceiling_color = COLOR_CEILING_MAZE
        self.floor_color = COLOR_FLOOR_MAZE

        # Per-column camera-space X in [-1, 1), reused by the floor caster.
        self._camera_x = 2.0 * (np.arange(self.width) + 0.5) / self.width - 1.0
        self._ys = np.arange(self.height)[:, None]  # (h, 1) column vector

        # Flattened texel table: all wall textures followed by half-brightness
        # copies (used for N/S faces), so draw_walls can gather every texel of
        # a frame with one flat index instead of a slow multi-array gather.
        n_tiles = atlas.wall_stack.shape[0]
        base = atlas.wall_stack[..., :3]
        self._n_tiles = n_tiles
        self._texel_table = np.concatenate([base, base >> 1]).reshape(-1, 3)

        self._texture = pyglet.image.Texture.create(self.width, self.height)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        self._sprite = pyglet.sprite.Sprite(self._texture)
        self._sprite.scale_x = SCREEN_WIDTH / self.width
        self._sprite.scale_y = SCREEN_HEIGHT / self.height

    @staticmethod
    def _camera_basis(angle: float) -> tuple[float, float, float, float]:
        """Return (dir_x, dir_y, plane_x, plane_y) for the given view angle."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        tan_hfov = math.tan(HALF_FOV)
        return cos_a, sin_a, -sin_a * tan_hfov, cos_a * tan_hfov

    def clear(self):
        """Fill the ceiling (top half). The floor half is drawn by draw_floor()."""
        self.fb[: self.height // 2, :, :3] = self.ceiling_color[:3]

    def draw_floor(self, player_x, player_y, player_angle, map_array, phase):
        """Draw the floor (bottom half). Solid fill for maze, per-pixel cast for bridge."""
        half = self.height // 2

        if phase == "maze":
            self.fb[half:, :, :3] = self.floor_color[:3]
            return

        dir_x, dir_y, plane_x, plane_y = self._camera_basis(player_angle)
        map_h, map_w = map_array.shape

        # Horizontal distance to the floor point seen at each screen row.
        p = np.maximum(1, np.arange(half, self.height) - half)
        row_dist = half / p  # (rows,)

        # World-space floor coordinates: outer product of row distance and
        # per-column ray direction.
        ray_x = dir_x + plane_x * self._camera_x  # (w,)
        ray_y = dir_y + plane_y * self._camera_x
        fx = player_x + row_dist[:, None] * ray_x[None, :]  # (rows, w)
        fy = player_y + row_dist[:, None] * ray_y[None, :]

        mx = np.floor(fx).astype(np.intp)
        my = np.floor(fy).astype(np.intp)
        in_bounds = (mx >= 0) & (mx < map_w) & (my >= 0) & (my < map_h)
        tile = map_array[my.clip(0, map_h - 1), mx.clip(0, map_w - 1)]

        color = _FLOOR_LUT[tile.clip(0, 8)]  # (rows, w, 3)

        checker = ((mx + my) & 1).astype(bool)
        is_bridge = tile == Tile.BRIDGE
        color[is_bridge & checker] = COLOR_BRIDGE_FLOOR_A
        color[is_bridge & ~checker] = COLOR_BRIDGE_FLOOR_B

        # Distance shading; the chasm instead darkens with depth to read as a void.
        shade = np.maximum(0.35, 1.0 - row_dist * 0.04)[:, None]
        chasm_shade = (1.0 - np.minimum(1.0, row_dist * 0.1) * 0.5)[:, None]
        factor = np.where(tile == Tile.CHASM, chasm_shade, shade)
        color *= factor[..., None]

        color[~in_bounds] = _OUT_OF_BOUNDS_COLOR
        self.fb[half:, :, :3] = color.astype(np.uint8)

    def draw_walls(self, dists, tiles, tex_xs, sides):
        """Draw textured wall columns from raycaster output arrays."""
        h = self.height
        self.depth[:] = dists

        visible = (tiles > 0) & (dists < 1e29)
        line_h = np.where(visible, h / np.maximum(dists, 1e-3), 0).astype(np.int64)
        start = h // 2 - line_h // 2  # may be negative when close to a wall

        rel = self._ys - start[None, :]  # (h, w) pixel offset within the column
        mask = visible[None, :] & (rel >= 0) & (rel < line_h[None, :])

        tex_y = (rel * TEX_SIZE // np.maximum(line_h, 1)[None, :]) & (TEX_SIZE - 1)
        # Texture index: shaded copies live n_tiles further along the table.
        tid = (tiles + self._n_tiles * sides)[None, :]
        idx = (tid * TEX_SIZE + tex_y) * TEX_SIZE + tex_xs[None, :]

        fb_rgb = self.fb[..., :3]
        fb_rgb[mask] = self._texel_table[idx[mask]]

    def draw_sprite(
        self,
        sprite_x: float,
        sprite_y: float,
        player_x: float,
        player_y: float,
        player_angle: float,
        sprite_data: np.ndarray,
        sprite_size: int,
    ):
        """Draw a billboarded sprite, depth-clipped per column against walls."""
        dir_x, dir_y, plane_x, plane_y = self._camera_basis(player_angle)

        dx = sprite_x - player_x
        dy = sprite_y - player_y

        # Transform into camera space: trans_y is perpendicular depth,
        # matching what the raycaster stores in the depth buffer.
        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y)
        trans_x = inv_det * (dir_y * dx - dir_x * dy)
        trans_y = inv_det * (-plane_y * dx + plane_x * dy)

        if trans_y < 0.1:
            return

        h, w = self.height, self.width
        screen_x = int((w / 2) * (1 + trans_x / trans_y))
        sprite_h = int(h / trans_y)
        sprite_w = sprite_h
        if sprite_h < 1:
            return

        start_x = screen_x - sprite_w // 2
        start_y = h // 2 - sprite_h // 2

        xs = np.arange(max(0, start_x), min(w, start_x + sprite_w))
        ys = np.arange(max(0, start_y), min(h, start_y + sprite_h))
        if xs.size == 0 or ys.size == 0:
            return

        col_visible = trans_y < self.depth[xs]
        if not col_visible.any():
            return

        tex_x = (xs - start_x) * sprite_size // sprite_w
        tex_y = (ys - start_y) * sprite_size // sprite_h
        sample = sprite_data[tex_y[:, None], tex_x[None, :]]  # (ny, nx, 4)

        mask = (sample[..., 3] >= 128) & col_visible[None, :]
        region = self.fb[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1, :3]
        region[mask] = sample[..., :3][mask]

    def upload_and_draw(self):
        """Upload framebuffer to GPU and draw scaled to screen."""
        img_data = pyglet.image.ImageData(
            self.width, self.height, "RGBA", self.fb.tobytes(),
            pitch=-self.stride,  # negative pitch: rows are top-to-bottom
        )
        self._texture.blit_into(img_data, 0, 0, 0)
        self._sprite.image = self._texture
        self._sprite.draw()
