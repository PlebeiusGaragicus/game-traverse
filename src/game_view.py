"""Game views: title screen and the main game loop."""

from __future__ import annotations

import copy
import math

import arcade
import numpy as np

from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HOLD_TO_QUIT_SECONDS,
    MAX_HEALTH, IFRAME_SECONDS, HIT_FLASH_SECONDS,
    MOUSE_SENSITIVITY, BOB_FREQUENCY, BOB_AMPLITUDE,
    MINIMAP_SCALE, MINIMAP_REVEAL, FIREBALL_ANIM_FPS,
)
from src.audio import SoundBank
from src.textures import TextureAtlas
from src.raycaster import cast_rays
from src.renderer import Renderer
from src.player import Player
from src.entities import EntityManager
from src.map_data import LEVELS, find_emitters


class TitleView(arcade.View):
    def __init__(self):
        super().__init__()
        cx = SCREEN_WIDTH / 2
        self._texts = [
            arcade.Text("TRAVERSE", cx, SCREEN_HEIGHT * 0.66, (255, 170, 60), 72,
                        anchor_x="center", anchor_y="center", bold=True),
            arcade.Text("Escape the maze. Survive the gauntlet. Cross the chasm.",
                        cx, SCREEN_HEIGHT * 0.52, (200, 200, 200), 18,
                        anchor_x="center", anchor_y="center"),
            arcade.Text("WASD move   ·   mouse or arrows turn   ·   TAB minimap   ·   hold ESC to quit",
                        cx, SCREEN_HEIGHT * 0.36, (150, 150, 150), 14,
                        anchor_x="center", anchor_y="center"),
            arcade.Text("Press any key to begin", cx, SCREEN_HEIGHT * 0.25,
                        (120, 220, 160), 20, anchor_x="center", anchor_y="center"),
        ]

    def on_show_view(self):
        arcade.set_background_color((0, 0, 0))
        self.window.set_exclusive_mouse(False)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.close()
            return
        self.window.show_view(GameView())

    def on_mouse_press(self, x, y, button, modifiers):
        self.window.show_view(GameView())

    def on_draw(self):
        self.clear()
        for text in self._texts:
            text.draw()


class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        self.atlas = TextureAtlas()
        self.renderer = Renderer(self.atlas)
        self.sounds = SoundBank()

        self.move_fwd = False
        self.move_back = False
        self.strafe_left = False
        self.strafe_right = False
        self.turn_left = False
        self.turn_right = False

        self.esc_pressed = False
        self.esc_held = 0.0

        self.time = 0.0
        self.won = False
        self.win_timer = 0.0
        self.minimap_on = False
        self.bob_phase = 0.0
        self.bob_scale = 0.0

        self._phase_text = arcade.Text(
            "", 10, SCREEN_HEIGHT - 30, (200, 200, 200, 180), 18, bold=True,
        )
        self._intro_text = arcade.Text(
            "", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 120,
            (255, 200, 120), 32, anchor_x="center", anchor_y="center", bold=True,
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
            "Press any key for the title screen", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20,
            (200, 200, 200), 18, anchor_x="center", anchor_y="center",
        )

        self._load_level(0)

    # ----- level / respawn management -----

    def _load_level(self, index: int, checkpoint: tuple | None = None):
        level = LEVELS[index]
        self.level_index = index
        self.level = level
        self.grid = copy.deepcopy(level.grid)
        self.map_h = len(self.grid)
        self.map_w = len(self.grid[0])
        self.map_array = np.array(level.grid, dtype=np.intp)

        emitter_data = find_emitters(self.grid, level.emitter_dirs)
        self.entities = EntityManager(
            emitter_data, *level.portal, emitter_timing=level.emitter_timing,
        )
        self.entities.on_spawn = self._on_fireball_spawn

        if checkpoint is None:
            x, y, angle = level.start
            checkpoint = (level.start_phase, x, y, angle)
            self.intro_timer = 2.2
            self._intro_text.text = f"LEVEL {index + 1}: {level.name.upper()}"
        else:
            self.intro_timer = 0.0
        self.checkpoint = checkpoint

        phase_name, x, y, angle = checkpoint
        self.player = Player(x, y, angle)
        self._set_phase(phase_name)

        self.health = MAX_HEALTH
        self.iframes = 0.0
        self.flash = 0.0
        self.death_timer = 0.0
        self.visited = np.zeros((self.map_h, self.map_w), dtype=bool)
        self._reveal_around_player()

    def _set_phase(self, name: str):
        phase = self.level.phases[name]
        self.phase_name = name
        self.phase = phase
        self.renderer.ceiling_color = phase.ceiling
        self.renderer.floor_color = phase.floor
        self._phase_text.text = phase.label

    def _respawn(self):
        self._load_level(self.level_index, checkpoint=self.checkpoint)
        self._capture_mouse(True)

    def _advance_level(self):
        if self.level_index + 1 >= len(LEVELS):
            self.won = True
            self.sounds.play("win")
            self._capture_mouse(False)
        else:
            self.sounds.play("portal")
            self._load_level(self.level_index + 1)

    def _on_fireball_spawn(self, fb):
        self.sounds.play_at("fire", fb.x, fb.y, self.player.x, self.player.y)

    def _on_death(self):
        self.sounds.play("death")
        self._capture_mouse(False)

    def _capture_mouse(self, captured: bool):
        try:
            self.window.set_exclusive_mouse(captured)
        except Exception:
            pass

    def _reveal_around_player(self):
        gx, gy = int(self.player.x), int(self.player.y)
        r = MINIMAP_REVEAL
        self.visited[max(0, gy - r):gy + r + 1, max(0, gx - r):gx + r + 1] = True

    # ----- input -----

    def on_show_view(self):
        arcade.set_background_color((0, 0, 0))
        self._capture_mouse(True)

    def on_hide_view(self):
        self._capture_mouse(False)

    def on_key_press(self, key, modifiers):
        # ESC always means hold-to-quit, even on the death/win screens.
        if key == arcade.key.ESCAPE:
            self.esc_pressed = True
            return

        if not self.player.alive and self.death_timer > 0.5:
            self._respawn()
            return
        if self.won and self.win_timer > 0.5:
            self.window.show_view(TitleView())
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
        elif key == arcade.key.TAB:
            self.minimap_on = not self.minimap_on

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

    def on_mouse_motion(self, x, y, dx, dy):
        if self.player.alive and not self.won:
            self.player.angle += dx * MOUSE_SENSITIVITY

    # ----- update -----

    def _check_triggers(self):
        trigger = self.level.triggers.get((int(self.player.x), int(self.player.y)))
        if trigger is None:
            return
        if trigger["action"] == "teleport":
            self.player.x = trigger["x"]
            self.player.y = trigger["y"]
            self.player.angle = trigger["angle"]
            self._set_phase(trigger["phase"])
            # Phase transitions are checkpoints: death respawns here.
            self.checkpoint = (
                trigger["phase"], trigger["x"], trigger["y"], trigger["angle"],
            )

    def on_update(self, delta_time):
        if self.esc_pressed:
            self.esc_held += delta_time
            if self.esc_held >= HOLD_TO_QUIT_SECONDS:
                self.window.close()
                return

        if not self.player.alive:
            self.death_timer += delta_time
            return

        if self.won:
            self.win_timer += delta_time
            return

        self.time += delta_time
        self.iframes = max(0.0, self.iframes - delta_time)
        self.flash = max(0.0, self.flash - delta_time)
        self.intro_timer = max(0.0, self.intro_timer - delta_time)

        self.player.update(
            delta_time,
            self.move_fwd, self.move_back,
            self.strafe_left, self.strafe_right,
            self.turn_left, self.turn_right,
            self.grid, self.map_w, self.map_h,
        )

        # Head bob: advance while moving, ease out when still.
        moving = self.move_fwd or self.move_back or self.strafe_left or self.strafe_right
        if moving:
            self.bob_phase += delta_time * BOB_FREQUENCY
            self.bob_scale = min(1.0, self.bob_scale + delta_time * 6.0)
        else:
            self.bob_scale = max(0.0, self.bob_scale - delta_time * 6.0)

        if not self.player.alive:  # walked into the chasm
            self._on_death()
            return

        self._check_triggers()
        self._reveal_around_player()

        hit, portal_touch = self.entities.update(
            delta_time, self.grid, self.map_w, self.map_h,
            self.player.x, self.player.y,
        )

        if hit and self.iframes <= 0.0:
            self.health -= 1
            self.iframes = IFRAME_SECONDS
            self.flash = HIT_FLASH_SECONDS
            if self.health <= 0:
                self.player.alive = False
                self._on_death()
                return
            self.sounds.play("hit")

        if portal_touch:
            self._advance_level()

    # ----- draw -----

    def _draw_hearts(self):
        # Top-left under the phase label; the minimap owns the top-right.
        for i in range(MAX_HEALTH):
            cx = 24 + i * 36
            cy = SCREEN_HEIGHT - 64
            color = (220, 40, 40) if i < self.health else (70, 60, 60)
            arcade.draw_polygon_filled(
                [(cx, cy + 12), (cx + 10, cy), (cx, cy - 12), (cx - 10, cy)], color,
            )

    def on_draw(self):
        self.clear()

        horizon = int(round(math.sin(self.bob_phase * 2 * math.pi) * BOB_AMPLITUDE * self.bob_scale))

        dists, tiles, tex_xs, sides = cast_rays(
            self.player.x, self.player.y, self.player.angle,
            self.grid, self.map_w, self.map_h,
        )

        self.renderer.clear(horizon)
        self.renderer.draw_floor(
            self.player.x, self.player.y, self.player.angle,
            self.map_array, self.phase.floor_cast, horizon,
        )
        self.renderer.draw_walls(dists, tiles, tex_xs, sides, horizon)

        frame_base = int(self.time * FIREBALL_ANIM_FPS)
        for i, fb in enumerate(self.entities.fireballs):
            sprite = self.atlas.fireball_frames[(frame_base + i) % len(self.atlas.fireball_frames)]
            self.renderer.draw_sprite(
                fb.x, fb.y,
                self.player.x, self.player.y, self.player.angle,
                sprite, self.atlas.fireball_size, horizon,
            )

        self.renderer.draw_sprite(
            self.entities.portal.x, self.entities.portal.y,
            self.player.x, self.player.y, self.player.angle,
            self.atlas.portal_sprite, self.atlas.portal_size, horizon,
        )

        if self.minimap_on:
            self.renderer.draw_minimap(
                self.map_array, self.visited,
                self.player.x, self.player.y, MINIMAP_SCALE,
            )

        self.renderer.upload_and_draw()

        # HUD overlay (drawn on top of the raycaster framebuffer)
        self._phase_text.draw()
        self._draw_hearts()

        if self.flash > 0:
            alpha = int(130 * self.flash / HIT_FLASH_SECONDS)
            rect = arcade.XYWH(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
            arcade.draw_rect_filled(rect, (255, 40, 30, alpha))

        if self.intro_timer > 0:
            alpha = int(255 * min(1.0, self.intro_timer / 0.8))
            self._intro_text.color = (255, 200, 120, alpha)
            self._intro_text.draw()

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

        if self.won:
            overlay = arcade.XYWH(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
            arcade.draw_rect_filled(overlay, (0, 0, 0, 150))
            self._win_title.draw()
            if self.win_timer > 0.5:
                self._win_hint.draw()
