"""Main game view: ties together raycaster, renderer, player, entities, and HUD."""

from __future__ import annotations

import arcade

from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HOLD_TO_QUIT_SECONDS,
    COLOR_CEILING_MAZE, COLOR_FLOOR_MAZE,
    COLOR_CEILING_BRIDGE, COLOR_FLOOR_BRIDGE,
)
from src.textures import TextureAtlas
from src.raycaster import cast_rays
from src.renderer import Renderer
from src.player import Player
from src.entities import EntityManager
from src.map_data import (
    LEVEL_1, LEVEL_1_WIDTH, LEVEL_1_HEIGHT,
    PLAYER_START_X, PLAYER_START_Y, PLAYER_START_ANGLE,
    PORTAL_X, PORTAL_Y,
    find_emitters, Tile,
)


class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        self.atlas = TextureAtlas()
        self.renderer = Renderer(self.atlas)

        self.world_map = LEVEL_1
        self.map_w = LEVEL_1_WIDTH
        self.map_h = LEVEL_1_HEIGHT

        self.player = Player(PLAYER_START_X, PLAYER_START_Y, PLAYER_START_ANGLE)

        emitter_data = find_emitters(self.world_map)
        self.entities = EntityManager(emitter_data, PORTAL_X, PORTAL_Y)

        self.move_fwd = False
        self.move_back = False
        self.strafe_left = False
        self.strafe_right = False
        self.turn_left = False
        self.turn_right = False

        self.esc_pressed = False
        self.esc_held = 0.0

        self.phase = "maze"
        self.death_timer = 0.0
        self.win_timer = 0.0

        self._phase_text = arcade.Text(
            "THE MAZE", 10, SCREEN_HEIGHT - 30,
            (200, 200, 200, 180), 18, bold=True,
        )
        self._death_title = arcade.Text(
            "YOU DIED", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40,
            arcade.color.RED, 48, anchor_x="center", anchor_y="center", bold=True,
        )
        self._death_hint = arcade.Text(
            "Press any key to retry", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20,
            (200, 200, 200), 18, anchor_x="center", anchor_y="center",
        )
        self._win_title = arcade.Text(
            "YOU ESCAPED!", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40,
            (100, 255, 150), 48, anchor_x="center", anchor_y="center", bold=True,
        )
        self._win_hint = arcade.Text(
            "Press any key to exit", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20,
            (200, 200, 200), 18, anchor_x="center", anchor_y="center",
        )

    def on_show_view(self):
        arcade.set_background_color((0, 0, 0))

    def on_key_press(self, key, modifiers):
        if not self.player.alive and self.death_timer > 0.5:
            self._restart()
            return
        if self.player.won and self.win_timer > 0.5:
            self.window.close()
            return

        if key == arcade.key.W:
            self.move_fwd = True
        elif key == arcade.key.S:
            self.move_back = True
        elif key == arcade.key.A:
            self.strafe_left = True
        elif key == arcade.key.D:
            self.strafe_right = True
        elif key == arcade.key.LEFT:
            self.turn_left = True
        elif key == arcade.key.RIGHT:
            self.turn_right = True
        elif key == arcade.key.ESCAPE:
            self.esc_pressed = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.W:
            self.move_fwd = False
        elif key == arcade.key.S:
            self.move_back = False
        elif key == arcade.key.A:
            self.strafe_left = False
        elif key == arcade.key.D:
            self.strafe_right = False
        elif key == arcade.key.LEFT:
            self.turn_left = False
        elif key == arcade.key.RIGHT:
            self.turn_right = False
        elif key == arcade.key.ESCAPE:
            self.esc_pressed = False
            self.esc_held = 0.0

    def _restart(self):
        self.player = Player(PLAYER_START_X, PLAYER_START_Y, PLAYER_START_ANGLE)
        emitter_data = find_emitters(self.world_map)
        self.entities = EntityManager(emitter_data, PORTAL_X, PORTAL_Y)
        self.phase = "maze"
        self.death_timer = 0.0
        self.win_timer = 0.0

    def on_update(self, delta_time):
        if self.esc_pressed:
            self.esc_held += delta_time
            if self.esc_held >= HOLD_TO_QUIT_SECONDS:
                self.window.close()
                return

        if not self.player.alive:
            self.death_timer += delta_time
            return

        if self.player.won:
            self.win_timer += delta_time
            return

        self.player.update(
            delta_time,
            self.move_fwd, self.move_back,
            self.strafe_left, self.strafe_right,
            self.turn_left, self.turn_right,
            self.world_map, self.map_w, self.map_h,
        )

        if not self.player.alive:
            return

        # Check phase transition: door tile sets player.won, but we intercept for maze->bridge
        if self.player.won and self.phase == "maze":
            self.player.won = False
            self.phase = "bridge"
            # Teleport player to bridge entrance
            self.player.x = 27.5
            self.player.y = 20.5
            self.player.angle = 1.5708  # facing south (positive Y)

        hit, portal_touch = self.entities.update(
            delta_time, self.world_map, self.map_w, self.map_h,
            self.player.x, self.player.y,
        )

        if hit:
            self.player.alive = False

        if portal_touch:
            self.player.won = True

        # Update ceiling/floor colors based on player position
        py_int = int(self.player.y)
        if py_int >= 20:
            self.renderer.ceiling_color = COLOR_CEILING_BRIDGE
            self.renderer.floor_color = COLOR_FLOOR_BRIDGE
        else:
            self.renderer.ceiling_color = COLOR_CEILING_MAZE
            self.renderer.floor_color = COLOR_FLOOR_MAZE

    def on_draw(self):
        self.clear()

        ray_results = cast_rays(
            self.player.x, self.player.y, self.player.angle,
            self.world_map, self.map_w, self.map_h,
        )

        self.renderer.clear()
        self.renderer.draw_walls(ray_results)

        # Draw fireballs as sprites
        for fb in self.entities.fireballs:
            self.renderer.draw_sprite(
                fb.x, fb.y,
                self.player.x, self.player.y, self.player.angle,
                self.atlas.fireball_sprite, self.atlas.fireball_size,
            )

        # Draw portal
        self.renderer.draw_sprite(
            self.entities.portal.x, self.entities.portal.y,
            self.player.x, self.player.y, self.player.angle,
            self.atlas.portal_sprite, self.atlas.portal_size,
        )

        self.renderer.upload_and_draw()

        # HUD overlay (drawn on top of the raycaster framebuffer)
        if self.phase == "maze":
            self._phase_text.text = "THE MAZE"
        else:
            self._phase_text.text = "THE BRIDGE"
        self._phase_text.draw()

        if self.esc_held > 0:
            bar_w = 200 * (self.esc_held / HOLD_TO_QUIT_SECONDS)
            bar = arcade.XYWH(SCREEN_WIDTH / 2, 20, bar_w, 8)
            arcade.draw_rect_filled(bar, arcade.color.ORANGE)

        if not self.player.alive:
            overlay = arcade.XYWH(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
            arcade.draw_rect_filled(overlay, (0, 0, 0, 150))
            self._death_title.draw()
            if self.death_timer > 0.5:
                self._death_hint.draw()

        if self.player.won:
            overlay = arcade.XYWH(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
            arcade.draw_rect_filled(overlay, (0, 0, 0, 150))
            self._win_title.draw()
            if self.win_timer > 0.5:
                self._win_hint.draw()
