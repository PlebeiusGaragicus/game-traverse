"""Framebuffer renderer: draws raycaster output and sprites, uploads to pyglet texture."""

from __future__ import annotations

import math

import pyglet
from pyglet.gl import GL_NEAREST, GL_RGBA, GL_UNSIGNED_BYTE, glTexParameteri, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER

from src.config import (
    RENDER_WIDTH, RENDER_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT,
    TEX_SIZE, COLOR_CEILING_MAZE, COLOR_FLOOR_MAZE,
)
from src.textures import TextureAtlas


class Renderer:
    def __init__(self, atlas: TextureAtlas):
        self.atlas = atlas
        self.width = RENDER_WIDTH
        self.height = RENDER_HEIGHT
        self.stride = self.width * 4
        self.buf = bytearray(self.width * self.height * 4)
        self.depth_buffer = [0.0] * self.width

        self.ceiling_color = COLOR_CEILING_MAZE
        self.floor_color = COLOR_FLOOR_MAZE

        self._texture = pyglet.image.Texture.create(self.width, self.height)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        self._sprite = pyglet.sprite.Sprite(self._texture)
        self._sprite.scale_x = SCREEN_WIDTH / self.width
        self._sprite.scale_y = SCREEN_HEIGHT / self.height

    def clear(self):
        """Fill ceiling and floor halves."""
        cr, cg, cb, ca = self.ceiling_color
        fr, fg, fb, fa = self.floor_color
        half = self.height // 2
        buf = self.buf
        w4 = self.width * 4
        for y in range(self.height):
            if y < half:
                r, g, b, a = cr, cg, cb, ca
            else:
                r, g, b, a = fr, fg, fb, fa
            row_start = y * w4
            for x in range(self.width):
                idx = row_start + x * 4
                buf[idx] = r
                buf[idx + 1] = g
                buf[idx + 2] = b
                buf[idx + 3] = a

    def draw_walls(self, ray_results: list[tuple[float, int, int, int]]):
        """Draw textured wall columns from raycaster output."""
        h = self.height
        buf = self.buf
        w4 = self.width * 4
        atlas = self.atlas

        for col, (dist, tile_id, tex_x, side) in enumerate(ray_results):
            self.depth_buffer[col] = dist

            if tile_id == 0 or dist >= 1e29:
                continue

            line_height = int(h / dist) if dist > 0.001 else h * 4
            draw_start = max(0, h // 2 - line_height // 2)
            draw_end = min(h - 1, h // 2 + line_height // 2)

            tex = atlas.get_wall(tile_id)
            if tex is None:
                continue

            for y in range(draw_start, draw_end + 1):
                tex_y_f = (y - (h // 2 - line_height // 2)) / line_height
                tex_y = int(tex_y_f * TEX_SIZE) & (TEX_SIZE - 1)

                t_idx = (tex_y * TEX_SIZE + tex_x) * 4
                r = tex[t_idx]
                g = tex[t_idx + 1]
                b = tex[t_idx + 2]

                if side == 1:
                    r = r >> 1
                    g = g >> 1
                    b = b >> 1

                fb_y = (h - 1) - y
                idx = fb_y * w4 + col * 4
                buf[idx] = r
                buf[idx + 1] = g
                buf[idx + 2] = b
                buf[idx + 3] = 255

    def draw_sprite(
        self,
        sprite_x: float,
        sprite_y: float,
        player_x: float,
        player_y: float,
        player_angle: float,
        sprite_data: bytearray,
        sprite_size: int,
    ):
        """Draw a billboarded sprite into the framebuffer, clipped by depth buffer."""
        dx = sprite_x - player_x
        dy = sprite_y - player_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.1:
            return

        sprite_angle = math.atan2(dy, dx) - player_angle
        while sprite_angle > math.pi:
            sprite_angle -= 2 * math.pi
        while sprite_angle < -math.pi:
            sprite_angle += 2 * math.pi

        if abs(sprite_angle) > math.pi / 2:
            return

        h = self.height
        w = self.width

        screen_x = int((0.5 + sprite_angle / (math.pi / 3)) * w)
        sprite_screen_h = int(h / dist) if dist > 0.1 else h * 4
        sprite_screen_w = sprite_screen_h

        start_x = screen_x - sprite_screen_w // 2
        start_y = h // 2 - sprite_screen_h // 2

        buf = self.buf
        w4 = w * 4

        for sx in range(sprite_screen_w):
            draw_x = start_x + sx
            if draw_x < 0 or draw_x >= w:
                continue
            if dist >= self.depth_buffer[draw_x]:
                continue

            tex_x = (sx * sprite_size) // sprite_screen_w
            if tex_x < 0 or tex_x >= sprite_size:
                continue

            for sy in range(sprite_screen_h):
                draw_y = start_y + sy
                if draw_y < 0 or draw_y >= h:
                    continue

                tex_y = (sy * sprite_size) // sprite_screen_h
                if tex_y < 0 or tex_y >= sprite_size:
                    continue

                t_idx = (tex_y * sprite_size + tex_x) * 4
                a = sprite_data[t_idx + 3]
                if a < 128:
                    continue

                fb_y = (h - 1) - draw_y
                idx = fb_y * w4 + draw_x * 4
                buf[idx] = sprite_data[t_idx]
                buf[idx + 1] = sprite_data[t_idx + 1]
                buf[idx + 2] = sprite_data[t_idx + 2]
                buf[idx + 3] = 255

    def upload_and_draw(self):
        """Upload framebuffer to GPU and draw scaled to screen."""
        img_data = pyglet.image.ImageData(
            self.width, self.height, "RGBA", bytes(self.buf), pitch=self.stride,
        )
        self._texture.blit_into(img_data, 0, 0, 0)
        self._sprite.image = self._texture
        self._sprite.draw()
