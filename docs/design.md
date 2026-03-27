# Traverse -- Design

## Overview

Retro Wolfenstein-style raycaster FPS in two phases:

1. **Maze**: navigate a grid-based maze to find the exit door
2. **Bridge**: traverse a narrow path over a chasm dodging fireballs from wall emitters

Win: reach the portal at the bridge's far end. Death: fireball hit or falling off the bridge.

## Rendering

- 320x200 internal resolution, nearest-neighbor scaled to 1280x720
- DDA raycasting, one ray per column
- 64x64 procedural wall textures
- Billboarded sprites for fireballs and portal
- Solid-color floor/ceiling (no floor casting)

## Map

2D integer grid. Tile types: empty, wall variants (stone/brick/metal/lava), door, bridge floor, emitter wall, chasm.

## Controls

WASD move/strafe, arrows turn, ESC hold to quit. No vertical look.
