# Traverse -- Design

## Overview

Retro Wolfenstein-style raycaster FPS in two phases:

1. **Maze**: navigate a grid-based maze to find the exit door
2. **Bridge**: traverse a narrow path over a chasm dodging fireballs from wall emitters

Win: reach the portal at the bridge's far end. Death: fireball hit or falling off the bridge.

## Rendering

- 320x200 internal resolution, nearest-neighbor scaled to 1280x720
- DDA raycasting, one ray per column; framebuffer composed with numpy
  (vectorized wall/floor/sprite drawing, ~3-4 ms/frame in pure Python + numpy)
- Framebuffer is top-down row order, uploaded with negative pitch (no Y flips
  in draw code)
- 64x64 procedural wall textures
- Billboarded sprites for fireballs and portal, camera-plane projection with
  perpendicular depth (consistent with wall occlusion)
- Solid-color floor/ceiling in the maze; per-pixel floor casting on the bridge

## Map

2D integer grid. Tile types: empty, wall variants (stone/brick/metal/lava), door, bridge floor, emitter wall, chasm.

Door tiles are inert by themselves; `TRIGGERS` in `map_data.py` maps tile
coordinates to actions (`teleport` for phase transitions, `win`). Emitters are
auto-discovered from the grid and fire toward the adjacent walkable tile.

## Controls

WASD move/strafe, arrows turn, ESC hold to quit. No vertical look.
