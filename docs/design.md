# Traverse -- Design

## Overview

Retro Wolfenstein-style raycaster FPS across three levels:

1. **The Maze**: navigate a grid maze to the exit door, then cross a bridge
   over a chasm (two phases, checkpoint at the transition)
2. **The Gauntlet**: serpentine corridors, each swept by an emitter; dodge
   into alcoves or outrun the fireballs
3. **The Crossing**: branching bridges over an open chasm with emitter
   pillars firing across the paths

Touching a level's portal advances to the next (wins on the last). The player
has 3 hearts with a brief invulnerability window per hit; falling into the
chasm is instant death. Death respawns at the current checkpoint. Emitters
glow (texture swap 7<->9) for 0.6s before firing, and all sound effects are
synthesized at startup via pyglet (no audio assets).

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

WASD move/strafe, mouse or arrows turn (exclusive mouse capture during play),
TAB toggles a fog-of-war minimap, ESC hold to quit. No vertical look; head
bob offsets the horizon a few pixels while moving.
