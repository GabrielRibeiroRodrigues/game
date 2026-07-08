from PIL import Image

# ── Palette ────────────────────────────────────────────────────────────────────
T   = (0,   0,   0,   0)   # transparent
SK  = (238, 182, 120, 255)  # skin
SD  = (196, 145,  88, 255)  # skin shadow
HR  = ( 35,  18,   8, 255)  # hair dark
HM  = ( 68,  40,  14, 255)  # hair mid
HL  = (105,  65,  22, 255)  # hair highlight
JK  = (155,  75, 210, 255)  # jacket purple
JD  = (112,  50, 165, 255)  # jacket dark
JL  = (192, 110, 240, 255)  # jacket light
WH  = (252, 248, 240, 255)  # white shirt
WS  = (215, 210, 200, 255)  # white shirt shadow
JN  = ( 55,  88, 168, 255)  # jeans blue
JNL = ( 82, 120, 205, 255)  # jeans light
JND = ( 38,  62, 128, 255)  # jeans dark
SH  = (245, 243, 238, 255)  # shoe white
SS  = (190, 188, 180, 255)  # shoe shadow
EY  = ( 22,  14,   6, 255)  # eye pupil
EW  = (255, 255, 255, 255)  # eye white
LI  = (218, 128, 108, 255)  # lip
BT  = (192, 155,  75, 255)  # belt gold

SHEET_W = 224
SHEET_H = 96
sheet = Image.new("RGBA", (SHEET_W, SHEET_H), T)


def px(sx, sy, c):
    if 0 <= sx < SHEET_W and 0 <= sy < SHEET_H:
        sheet.putpixel((sx, sy), c)


def rc(x1, y1, x2, y2, c, ox=0, oy=0):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            px(x + ox, y + oy, c)


def ln(x, y1, y2, c, ox=0, oy=0):
    for y in range(y1, y2 + 1):
        px(x + ox, y + oy, c)


def rl(y, x1, x2, c, ox=0, oy=0):
    for x in range(x1, x2 + 1):
        px(x + ox, y + oy, c)


def draw_small(ox, oy, lt=0, rt=0, la=0, ra=0, lean=0, cr=0, jump=False):
    """Draw a 32x32 character frame into the sheet at pixel offset (ox, oy)."""
    bx = 14 + lean  # body centre x in frame

    # ── Hair ──────────────────────────────────────────────────────────────────
    rc(bx - 8, 4 + cr, bx - 4, 12 + cr, HR, ox, oy)
    rc(bx - 9, 5 + cr, bx - 5, 11 + cr, HR, ox, oy)
    ln(bx - 8, 5 + cr, 10 + cr, HM, ox, oy)
    rc(bx - 4, 3 + cr, bx + 3,  6 + cr, HR, ox, oy)
    rl(3 + cr, bx - 2, bx + 1, HM, ox, oy)

    # ── Face ──────────────────────────────────────────────────────────────────
    rc(bx - 3, 5 + cr, bx + 4, 12 + cr, SK, ox, oy)
    ln(bx + 3,  6 + cr, 11 + cr, SD, ox, oy)
    ln(bx + 4,  6 + cr, 11 + cr, SD, ox, oy)
    ln(bx - 3,  5 + cr, 11 + cr, HR, ox, oy)

    # Eyebrow
    rl(7 + cr, bx + 1, bx + 3, HM, ox, oy)
    # Eye white
    rc(bx + 1, 8 + cr, bx + 3, 9 + cr, EW, ox, oy)
    # Pupil
    px(bx + 2 + ox, 8  + cr + oy, EY)
    px(bx + 2 + ox, 9  + cr + oy, EY)
    px(bx + 1 + ox, 8  + cr + oy, EY)
    # Nose hint
    px(bx + 2 + ox, 11 + cr + oy, SD)
    # Lip
    rl(12 + cr, bx, bx + 2, LI, ox, oy)

    # ── Neck ──────────────────────────────────────────────────────────────────
    rc(bx - 1, 13 + cr, bx + 1, 14 + cr, SK, ox, oy)

    # ── Collar / shirt ────────────────────────────────────────────────────────
    rc(bx - 2, 14 + cr, bx + 3, 15 + cr, WH, ox, oy)

    # ── Jacket ────────────────────────────────────────────────────────────────
    rc(bx - 4, 15 + cr, bx + 5, 22 + cr, JK, ox, oy)
    ln(bx - 4, 15 + cr, 22 + cr, JD, ox, oy)
    ln(bx - 3, 15 + cr, 22 + cr, JD, ox, oy)
    ln(bx + 5, 15 + cr, 22 + cr, JD, ox, oy)
    ln(bx,     15 + cr, 20 + cr, JL, ox, oy)
    rc(bx - 1, 15 + cr, bx + 2, 18 + cr, WH, ox, oy)
    ln(bx - 1, 15 + cr, 18 + cr, WS, ox, oy)

    # ── Left arm (screen-right) ────────────────────────────────────────────────
    lab = 16 + cr + la
    rc(bx + 5, lab,     bx + 7, lab + 5, JD, ox, oy)
    rc(bx + 5, lab + 5, bx + 7, lab + 7, SK, ox, oy)

    # ── Right arm (screen-left) ───────────────────────────────────────────────
    rab = 16 + cr + ra
    rc(bx - 7, rab,     bx - 5, rab + 5, JK, ox, oy)
    rc(bx - 7, rab + 5, bx - 5, rab + 7, SK, ox, oy)

    # ── Belt ──────────────────────────────────────────────────────────────────
    rc(bx - 4, 21 + cr, bx + 5, 22 + cr, BT, ox, oy)

    # ── Legs ──────────────────────────────────────────────────────────────────
    llx = bx - 4 + lt
    rlx = bx + 1 + rt
    if jump:
        rc(llx,     23 + cr, llx + 3, 26 + cr, JN,  ox, oy)
        ln(llx,     23 + cr, 26 + cr, JNL, ox, oy)
        rc(llx - 3, 25 + cr, llx,     28 + cr, JND, ox, oy)
        rc(rlx,     23 + cr, rlx + 3, 26 + cr, JN,  ox, oy)
        ln(rlx,     23 + cr, 26 + cr, JNL, ox, oy)
        rc(rlx + 3, 25 + cr, rlx + 6, 28 + cr, JND, ox, oy)
        # shoes under bent legs
        rc(llx - 4, 27 + cr, llx + 1, 29 + cr, SH, ox, oy)
        rl(29 + cr, llx - 4, llx + 1, SS, ox, oy)
        rc(rlx + 2, 27 + cr, rlx + 7, 29 + cr, SH, ox, oy)
        rl(29 + cr, rlx + 2, rlx + 7, SS, ox, oy)
    else:
        rc(llx, 23 + cr, llx + 3, 29 + cr, JN, ox, oy)
        ln(llx, 23 + cr, 29 + cr, JNL, ox, oy)
        ln(llx + 3, 23 + cr, 29 + cr, JND, ox, oy)
        rc(rlx, 23 + cr, rlx + 3, 29 + cr, JN, ox, oy)
        ln(rlx, 23 + cr, 29 + cr, JNL, ox, oy)
        ln(rlx + 3, 23 + cr, 29 + cr, JND, ox, oy)
        # shoes
        lsx = bx - 5 + lt
        rc(lsx, 29 + cr, lsx + 5, 31 + cr, SH, ox, oy)
        rl(31 + cr, lsx, lsx + 5, SS, ox, oy)
        rsx = bx + rt
        rc(rsx, 29 + cr, rsx + 5, 31 + cr, SH, ox, oy)
        rl(31 + cr, rsx, rsx + 5, SS, ox, oy)


def draw_big(ox, lt=0, rt=0, la=0, ra=0, lean=0, cr=0, jump=False):
    """Draw 32x64 big character at sheet row oy=32."""
    oy = 32
    bx = 14 + lean

    # ── Hair ──────────────────────────────────────────────────────────────────
    rc(bx - 9, 2 + cr, bx - 4, 17 + cr, HR, ox, oy)
    rc(bx - 10, 3 + cr, bx - 5, 16 + cr, HR, ox, oy)
    ln(bx - 9, 4 + cr, 15 + cr, HM, ox, oy)
    rc(bx - 4, 2 + cr, bx + 3,  7 + cr, HR, ox, oy)
    rl(2 + cr, bx - 2, bx + 1, HM, ox, oy)

    # ── Face ──────────────────────────────────────────────────────────────────
    rc(bx - 3, 4 + cr, bx + 5, 17 + cr, SK, ox, oy)
    ln(bx + 4,  5 + cr, 16 + cr, SD, ox, oy)
    ln(bx + 5,  5 + cr, 16 + cr, SD, ox, oy)
    ln(bx - 3,  4 + cr, 16 + cr, HR, ox, oy)

    rl(8  + cr, bx + 1, bx + 4, HM, ox, oy)
    rc(bx + 1, 9 + cr, bx + 4, 11 + cr, EW, ox, oy)
    px(bx + 2 + ox, 10 + cr + oy, EY)
    px(bx + 3 + ox, 10 + cr + oy, EY)
    px(bx + 1 + ox,  9 + cr + oy, EY)
    px(bx + 2 + ox, 14 + cr + oy, SD)
    rl(16 + cr, bx, bx + 2, LI, ox, oy)

    # ── Neck ──────────────────────────────────────────────────────────────────
    rc(bx - 1, 17 + cr, bx + 2, 19 + cr, SK, ox, oy)

    # ── Collar ────────────────────────────────────────────────────────────────
    rc(bx - 3, 19 + cr, bx + 4, 21 + cr, WH, ox, oy)

    # ── Jacket ────────────────────────────────────────────────────────────────
    rc(bx - 5, 21 + cr, bx + 6, 36 + cr, JK, ox, oy)
    ln(bx - 5, 21 + cr, 36 + cr, JD, ox, oy)
    ln(bx - 4, 21 + cr, 36 + cr, JD, ox, oy)
    ln(bx + 6, 21 + cr, 36 + cr, JD, ox, oy)
    ln(bx,     21 + cr, 32 + cr, JL, ox, oy)
    rc(bx - 2, 21 + cr, bx + 3, 27 + cr, WH, ox, oy)
    ln(bx - 2, 21 + cr, 27 + cr, WS, ox, oy)

    # ── Arms ──────────────────────────────────────────────────────────────────
    lab = 23 + cr + la
    rc(bx + 6, lab,      bx + 9, lab + 9,  JD, ox, oy)
    rc(bx + 6, lab + 9,  bx + 9, lab + 12, SK, ox, oy)

    rab = 23 + cr + ra
    rc(bx - 9, rab,      bx - 6, rab + 9,  JK, ox, oy)
    rc(bx - 9, rab + 9,  bx - 6, rab + 12, SK, ox, oy)

    # ── Belt ──────────────────────────────────────────────────────────────────
    rc(bx - 5, 35 + cr, bx + 6, 37 + cr, BT, ox, oy)

    # ── Legs ──────────────────────────────────────────────────────────────────
    llx = bx - 5 + lt
    rlx = bx + 1 + rt
    rc(llx, 37 + cr, llx + 4, 52 + cr, JN,  ox, oy)
    ln(llx, 37 + cr, 52 + cr, JNL, ox, oy)
    ln(llx + 4, 37 + cr, 52 + cr, JND, ox, oy)
    rc(rlx, 37 + cr, rlx + 4, 52 + cr, JN,  ox, oy)
    ln(rlx, 37 + cr, 52 + cr, JNL, ox, oy)
    ln(rlx + 4, 37 + cr, 52 + cr, JND, ox, oy)

    # ── Shoes ─────────────────────────────────────────────────────────────────
    lsx = bx - 6 + lt
    rc(lsx, 51 + cr, lsx + 6, 55 + cr, SH, ox, oy)
    rl(55 + cr, lsx, lsx + 6, SS, ox, oy)
    rsx = bx + rt
    rc(rsx, 51 + cr, rsx + 6, 55 + cr, SH, ox, oy)
    rl(55 + cr, rsx, rsx + 6, SS, ox, oy)


# ── Small frames (oy=0) ───────────────────────────────────────────────────────
draw_small(ox=0,   oy=0)                                        # idle
draw_small(ox=32,  oy=0, lt=-3, rt=3,  la=3,  ra=-3)           # run1
draw_small(ox=64,  oy=0, lt=-1, rt=1,  la=1,  ra=-1)           # run2
draw_small(ox=96,  oy=0, lt=3,  rt=-3, la=-3, ra=3)            # run3
draw_small(ox=128, oy=0, jump=True, la=-4, ra=-4)               # jump
draw_small(ox=160, oy=0, lt=2,  rt=-2, la=2,  ra=-2, lean=-1)  # brake
draw_small(ox=192, oy=0, cr=3,  la=4,  ra=4)                   # dead/crouch

# ── Big frames (oy=32) ────────────────────────────────────────────────────────
draw_big(ox=0)
draw_big(ox=32,  lt=-4, rt=4,  la=4,  ra=-4)
draw_big(ox=64,  lt=-2, rt=2,  la=2,  ra=-2)
draw_big(ox=96,  lt=4,  rt=-4, la=-4, ra=4)
draw_big(ox=128, lt=0,  rt=0,  la=-5, ra=-5)
draw_big(ox=160, lt=2,  rt=-2, la=2,  ra=-2, lean=-1)

sheet.save("./img/yasmin_sprites.png")
print("Done: 224x96 RGBA sprite sheet saved.")
