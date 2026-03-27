"""Game constants."""

import math

TITLE = "Traverse"

# Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Internal raycaster resolution
RENDER_WIDTH = 320
RENDER_HEIGHT = 200

# Raycasting
FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2

# Player
MOVE_SPEED = 3.0        # units/sec
STRAFE_SPEED = 2.5      # units/sec
TURN_SPEED = 2.0         # rad/sec
PLAYER_RADIUS = 0.25     # collision radius in grid units

# Textures
TEX_SIZE = 64

# Fireballs
FIREBALL_SPEED = 2.5     # units/sec
FIREBALL_RADIUS = 0.3    # collision radius
EMITTER_COOLDOWN = 3.0   # seconds between spawns

# ESC
HOLD_TO_QUIT_SECONDS = 1.0

# Colors (RGBA tuples for framebuffer)
COLOR_CEILING_MAZE = (60, 60, 70, 255)
COLOR_FLOOR_MAZE = (90, 85, 80, 255)
COLOR_CEILING_BRIDGE = (20, 10, 10, 255)
COLOR_FLOOR_BRIDGE = (15, 10, 8, 255)
COLOR_CHASM = (5, 2, 2, 255)
