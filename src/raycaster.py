"""DDA raycaster -- casts one ray per screen column and returns hit info."""

import math

from src.config import RENDER_WIDTH, FOV, HALF_FOV

# Result tuple indices
R_DIST = 0
R_TILE = 1
R_TEX_X = 2
R_SIDE = 3  # 0 = E/W face, 1 = N/S face


def cast_rays(
    px: float,
    py: float,
    angle: float,
    world_map: list[list[int]],
    map_w: int,
    map_h: int,
) -> list[tuple[float, int, int, int]]:
    """
    Cast RENDER_WIDTH rays from player position and return per-column hit info.

    Returns list of (perp_distance, tile_id, tex_x_0_to_63, side).
    """
    results: list[tuple[float, int, int, int]] = []

    for col in range(RENDER_WIDTH):
        camera_x = 2.0 * col / RENDER_WIDTH - 1.0
        ray_angle = angle + math.atan2(camera_x * math.tan(HALF_FOV), 1.0)

        ray_dir_x = math.cos(ray_angle)
        ray_dir_y = math.sin(ray_angle)

        map_x = int(px)
        map_y = int(py)

        if ray_dir_x == 0:
            delta_dist_x = 1e30
        else:
            delta_dist_x = abs(1.0 / ray_dir_x)

        if ray_dir_y == 0:
            delta_dist_y = 1e30
        else:
            delta_dist_y = abs(1.0 / ray_dir_y)

        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (px - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - px) * delta_dist_x

        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (py - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - py) * delta_dist_y

        side = 0
        hit = False
        tile_id = 0
        max_steps = 64

        for _ in range(max_steps):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= map_w or map_y < 0 or map_y >= map_h:
                hit = True
                tile_id = 1
                break

            cell = world_map[map_y][map_x]
            if cell >= 1 and cell != 6 and cell != 8:
                hit = True
                tile_id = cell
                break

        if not hit:
            results.append((1e30, 0, 0, 0))
            continue

        if side == 0:
            perp_dist = side_dist_x - delta_dist_x
        else:
            perp_dist = side_dist_y - delta_dist_y

        if perp_dist < 0.001:
            perp_dist = 0.001

        # Correct fisheye: project onto camera plane
        perp_dist *= math.cos(ray_angle - angle)
        if perp_dist < 0.001:
            perp_dist = 0.001

        if side == 0:
            wall_x = py + perp_dist / math.cos(ray_angle - angle) * ray_dir_y
        else:
            wall_x = px + perp_dist / math.cos(ray_angle - angle) * ray_dir_x
        wall_x -= math.floor(wall_x)

        tex_x = int(wall_x * 64) & 63

        if side == 0 and ray_dir_x > 0:
            tex_x = 63 - tex_x
        if side == 1 and ray_dir_y < 0:
            tex_x = 63 - tex_x

        results.append((perp_dist, tile_id, tex_x, side))

    return results
