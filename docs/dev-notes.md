# Dev notes (agent-facing)

Terse reference for continuing development from a fresh context. Read this
before touching code. `design.md` covers the player-facing design.

## Run / test / verify

- Play: `../../run traverse` (repo-root script; no-arg `../../run` starts the Landus
  launcher UI instead) or `../../.venv/bin/python src/main.py` from this dir.
- Parent venv pip shebang is BROKEN (repo was moved); always `.venv/bin/python -m pip`, never `.venv/bin/pip`.
- Level validation: `../../.venv/bin/python tests/test_levels.py` — run after ANY map/level edit.
- macOS `screencapture` lacks permission. To see the live game, run it and capture in-process:
  `arcade.schedule(fn, 1/30)`; in fn call `view.on_key_press(...)` to drive input and
  `arcade.get_image().save(path)` to snapshot, then `window.close()`. Read the PNG.
- Headless rendering (no GL) for fast visual/perf checks: subclass `Renderer`, override
  `__init__` to skip pyglet texture setup (copy fields: fb, depth, _camera_x, _ys,
  _n_tiles, _texel_table, colors). Save fb as PPM, convert via `sips -s format png`.
- Sim gameplay without arcade: `Player` + `EntityManager` + `find_emitters` are pure logic;
  step with dt=1/60. GameView needs a window (arcade.Text in __init__).

## Coordinates & conventions

- Grid indexed `grid[y][x]`. x = east = column, y = south = row. angle 0 = +x (east),
  pi/2 = +y (south). No vertical look.
- Framebuffer `Renderer.fb` is (200, 320, 4) uint8, TOP-DOWN rows (row 0 = screen top),
  uploaded with negative pitch. Never flip Y in draw code.
- Internal res 320x200 (config RENDER_*), scaled to 1280x720 window.

## Tile IDs (map_data.Tile)

0 empty, 1 stone, 2 brick, 3 metal, 4 lava, 5 door(walkable), 6 bridge(walkable),
7 emitter wall, 8 chasm (kills on tile entry), 9 emitter-hot (RUNTIME ONLY —
EntityManager swaps 7<->9 in the live grid each frame for telegraph glow).
Walkable = {0,5,6} — encoded in THREE places: `map_data.WALKABLE`,
`Player._is_solid` (inverse), `Fireball.update` pass-through set {6,8,5}+(<1).
Keep them in sync if adding tiles. Raycaster wall test: `cell >= 1 and cell not in (6,8)`.

## Renderer (src/renderer.py) — all numpy, no per-pixel Python

- `_texel_table`: flat (2*n_tiles*64*64, 3); second half is pre-shaded (>>1) copies for
  N/S faces. Index = ((tile + n_tiles*side)*64 + tex_y)*64 + tex_x. n_tiles comes from
  atlas.wall_stack.shape[0] (currently 10). Adding a wall texture: bump n_tiles in
  TextureAtlas AND nothing else (table auto-builds).
- `_FLOOR_LUT` / `_MINIMAP_LUT` sized 10; grow if adding tile IDs (floor caster clips to 0..9).
- `horizon` param (head bob) on clear/draw_floor/draw_walls/draw_sprite: int px offset of
  horizon row, clamped ±8 in `_horizon_row`. Pass the same value to all four per frame.
- Sprites: camera-plane transform (`_camera_basis`), perp depth vs `self.depth` per column.
  Sprite draw order matters (painter's): fireballs then portal currently; fine because
  depth-clip vs walls only, sprites don't depth-test each other.
- Perf: ~3-4 ms/frame total at 320x200 (walls gather dominates ~2.6ms). Budget 16ms.
  If adding cost, benchmark headless first (see pattern above).
- Minimap: `draw_minimap` composites into fb top-right, scale px/tile, fog via `visited`
  bool array. Map must fit: rows*scale <= ~190. Level 1 is 34 rows @ scale 2 = 68 ok.

## Level system (src/map_data.py)

- `LEVELS: list[Level]`. Level = grid template (deep-copied by GameView._load_level),
  start (x,y,angle), start_phase, phases{name: Phase(label, ceiling, floor, floor_cast)},
  triggers{(gx,gy): {"action": "teleport", x,y,angle,phase}}, portal (x,y),
  emitter_dirs{(gx,gy): (dx,dy)} overrides, emitter_timing{(gx,gy): (period, first_delay)}.
- Portal touch => next level, or win on last. Triggers currently only "teleport";
  teleport also sets the respawn checkpoint (phase,x,y,angle).
- `find_emitters(grid, dir_overrides)`: direction = first adjacent {empty,bridge,chasm} in
  order E,W,S,N unless overridden. Pillars surrounded by chasm NEED an override to aim.
- Levels 2/3 are built by `_build_gauntlet()` / `_build_crossing()` (procedural carving —
  easier to keep valid than ASCII grids). Level 1 is a literal grid.
- After map edits ALWAYS run tests/test_levels.py (BFS reachability, emitter sanity).

## GameView (src/game_view.py)

- States: playing / dead (player.alive False) / won. Health lives on GameView not Player;
  Player.alive is only chasm/out-of-health. iframes (1s) gate fireball damage; hit flash 0.4s.
- `checkpoint` = (phase, x, y, angle); set at level load and by teleport triggers;
  `_respawn()` reloads current level at checkpoint (fresh grid deepcopy + entities, full health).
- `self.grid` (mutable, entities swap 7/9) vs `self.map_array` (numpy, from TEMPLATE, static —
  used by floor caster + minimap; intentionally doesn't show telegraph).
- Mouse: exclusive capture during play, released on death/win/title. ESC is reserved for
  hold-to-quit everywhere (never bind it to anything else).
- Fireball anim: atlas.fireball_frames[3], index (int(time*10)+i)%3.
- TitleView is the entry view (main.py); win screen returns to TitleView.

## Audio (src/audio.py)

- SoundBank synthesizes at startup (pyglet.media.synthesis), no assets, silently no-ops on
  failure. `play_at` = distance-attenuated. Spawn hiss wired via EntityManager.on_spawn callback.

## Landus integration

- game.json: entry `python src/main.py`, theme_song null, no cover_art key — the
  launcher draws a procedural cover. Re-add cover_art only once the file exists;
  the launcher's tests assert every declared asset path resolves.
- LANDUS_FULLSCREEN=1 env var → fullscreen (main.py). The launcher always sets it.
- Dependencies come from this repo's own `.venv`, provisioned by the parent's
  `./setup`. Per-game venvs: the launcher runs `.venv/bin/python` from here, not
  the launcher's interpreter.
- This is a git submodule; commit here first, then bump pointer in parent repo.

## Known gaps / natural next steps

- No cover art; the launcher shows a procedural placeholder. Add
  `assets/cover.png` plus the `cover_art` key together.
- No score/best-time tracking; win screen just returns to title.
- Emitter fire sound plays for ALL spawns each frame loop (fine at current emitter counts).
- Fireballs don't collide with each other or the player's movement (only radius check).
- test_levels.py doesn't validate that alcoves/branches are survivable, only reachable.
