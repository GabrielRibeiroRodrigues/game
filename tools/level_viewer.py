"""Renders level JSON files as top-down grid images for analysis."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

TILE = 10   # pixels per tile in the preview
ROWS = 15   # level grid rows

# Colors
C_SKY       = (135, 195, 235)  # playable air
C_GROUND    = (100, 72, 38)    # solid ground
C_DIRT      = (140, 100, 55)   # ground dirt row
C_ABYSS     = (15, 10, 20)     # void / death
C_PLATFORM  = (80, 160, 80)    # elevated solid tile
C_MPLATFORM = (60, 120, 220)   # moving platform (start pos)
C_PORTAL    = (80, 255, 130)   # end portal
C_ENEMY     = (220, 60, 60)    # goomba / koopa
C_COIN      = (255, 220, 50)   # coin / coinbox
C_PLAYER    = (200, 80, 220)   # player start
C_CAM_EDGE  = (255, 150, 0)    # camera right limit line


def render_level(name):
    path = f"./levels/{name}.json"
    with open(path) as f:
        data = json.load(f)

    length      = data["length"]
    sky_y       = data["level"]["layers"]["sky"]["y"]
    ground_y    = data["level"]["layers"]["ground"]["y"]
    sky_rows    = len(range(*sky_y))      # how many sky rows
    ground_rows = len(range(*ground_y))   # how many ground rows
    total_rows  = sky_rows + ground_rows  # 15

    # Build base grid
    # 0=sky, 1=ground, 2=ground_dirt
    grid = []
    for y in range(total_rows):
        row = []
        for x in range(length):
            if y < sky_rows:
                row.append("sky")
            elif y == sky_rows:
                row.append("ground")
            else:
                row.append("dirt")
        grid.append(row)

    objects = data["level"]["objects"]

    # Apply sky overrides (abysses)
    for x, y in objects.get("sky", []):
        if 0 <= y < total_rows and 0 <= x < length:
            grid[y][x] = "abyss"

    # Apply ground overrides (elevated platforms)
    for x, y in objects.get("ground", []):
        if 0 <= y < total_rows and 0 <= x < length:
            grid[y][x] = "platform"

    # --- Render image ---------------------------------------------------------
    W = length * TILE
    H = total_rows * TILE + 60   # extra space for legend below grid
    img = Image.new("RGB", (W, H), C_ABYSS)
    d   = ImageDraw.Draw(img)

    color_map = {
        "sky":      C_SKY,
        "abyss":    C_ABYSS,
        "ground":   C_GROUND,
        "dirt":     C_DIRT,
        "platform": C_PLATFORM,
    }

    for y in range(total_rows):
        for x in range(length):
            c = color_map[grid[y][x]]
            d.rectangle([x*TILE, y*TILE, x*TILE+TILE-1, y*TILE+TILE-1], fill=c)

    # Grid lines (subtle)
    for x in range(0, length, 5):
        d.line([(x*TILE, 0), (x*TILE, total_rows*TILE)], fill=(0,0,0,80), width=1)
    for y in range(total_rows):
        d.line([(0, y*TILE), (W, y*TILE)], fill=(0,0,0,80), width=1)

    # Camera scroll limit
    cam_limit = max(50, length - 10)
    cx = cam_limit * TILE
    d.line([(cx, 0), (cx, total_rows*TILE)], fill=C_CAM_EDGE, width=2)

    entities = data["level"].get("entities", {})

    # Moving platforms (blue)
    for mp in entities.get("MovingPlatform", []):
        mx, my = mp[0], mp[1]
        d.rectangle([mx*TILE, my*TILE, mx*TILE+TILE*2-1, my*TILE+TILE//2-1], fill=C_MPLATFORM)
        d.rectangle([mx*TILE, my*TILE, mx*TILE+TILE*2-1, my*TILE+TILE//2-1], outline=(20,20,180))

    # End portal
    for ex, ey in entities.get("EndPortal", []):
        d.rectangle([ex*TILE, ey*TILE, ex*TILE+TILE*2-1, (ey+2)*TILE-1], fill=C_PORTAL)

    # Enemies
    for ex, ey in entities.get("Goomba", []) + entities.get("Koopa", []):
        d.ellipse([ex*TILE+1, ey*TILE+1, ex*TILE+TILE-2, ey*TILE+TILE-2], fill=C_ENEMY)

    # Coins / CoinBoxes
    for ex, ey in entities.get("coin", []) + entities.get("CoinBox", []):
        d.rectangle([ex*TILE+2, ey*TILE+2, ex*TILE+TILE-3, ey*TILE+TILE-3], fill=C_COIN)

    # Player start (tile 0, row 12 = one above ground)
    d.ellipse([0, sky_rows*TILE - TILE, TILE-1, sky_rows*TILE-1], fill=C_PLAYER)

    # x-axis labels every 10 tiles
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    for x in range(0, length, 10):
        lbl = str(x)
        ty  = total_rows * TILE + 2
        d.text((x*TILE, ty), lbl, fill=(220,220,220), font=font)

    # Legend
    legend = [
        (C_SKY, "Sky"), (C_ABYSS, "Abyss"), (C_GROUND, "Ground"),
        (C_PLATFORM, "Platform"), (C_MPLATFORM, "Moving Platform"),
        (C_PORTAL, "End Portal"), (C_ENEMY, "Enemy"), (C_COIN, "Coin/Box"),
        (C_CAM_EDGE, "Cam limit"), (C_PLAYER, "Player"),
    ]
    lx = 2
    for color, label in legend:
        d.rectangle([lx, total_rows*TILE+22, lx+8, total_rows*TILE+30], fill=color)
        d.text((lx+10, total_rows*TILE+22), label, fill=(230,230,230), font=font)
        lx += len(label)*6 + 18

    out_path = f"./img/{name}_preview.png"
    img.save(out_path)
    print(f"Saved: {out_path}  ({W}x{H})")
    return out_path


if __name__ == "__main__":
    levels = ["Level1-1", "Level1-2", "Level2-1", "Level2-2"]
    for lvl in levels:
        try:
            render_level(lvl)
        except Exception as e:
            print(f"Error {lvl}: {e}")
