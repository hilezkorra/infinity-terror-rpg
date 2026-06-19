from PIL import Image, ImageDraw
import os

COLS = 8
ROWS = 5
W = COLS * 16
H = ROWS * 16
sheet = Image.new('RGBA', (W, H), (0,0,0,0))

def fr(img, ox,oy, x1,y1,x2,y2, color):
    d = ImageDraw.Draw(img)
    d.rectangle([ox+x1,oy+y1,ox+x2,oy+y2], fill=color)

def sp(col, row):
    return col*16, row*16

# ── ROW 0: Lab Equipment ──────────────────────────────────────────────────

# 0: Computer terminal (green phosphor)
ox,oy = sp(0,0)
fr(sheet,ox,oy, 2,2,13,13, (30,35,30,255))
fr(sheet,ox,oy, 3,3,12,10, (0,80,20,255))
fr(sheet,ox,oy, 4,4,11,9, (0,200,70,255))
for sy in [4,6,8]: fr(sheet,ox,oy, 5,sy,10,sy, (0,100,35,180))
fr(sheet,ox,oy, 6,11,9,12, (40,50,40,255))
fr(sheet,ox,oy, 4,13,11,14, (35,40,35,255))

# 1: Server rack
ox,oy = sp(1,0)
fr(sheet,ox,oy, 3,1,12,14, (25,30,35,255))
fr(sheet,ox,oy, 4,2,11,13, (18,22,28,255))
for ry in [3,5,7,9,11]:
    fr(sheet,ox,oy, 5,ry,11,ry+1, (0,80,160,100))
    fr(sheet,ox,oy, 10,ry,11,ry, (0,220,80,200))

# 2: Specimen jar (glowing green)
ox,oy = sp(2,0)
fr(sheet,ox,oy, 5,1,10,2, (80,90,80,255))
fr(sheet,ox,oy, 4,2,11,13, (20,60,30,180))
fr(sheet,ox,oy, 5,3,10,12, (0,120,20,220))
fr(sheet,ox,oy, 6,5,9,10, (50,200,60,255))
fr(sheet,ox,oy, 7,6,8,9, (200,240,100,255))
fr(sheet,ox,oy, 4,13,11,14, (60,70,60,255))

# 3: Lab table (overhead)
ox,oy = sp(3,0)
fr(sheet,ox,oy, 1,4,14,11, (40,45,50,255))
fr(sheet,ox,oy, 1,4,14,5, (70,80,90,255))
fr(sheet,ox,oy, 1,11,14,12, (20,25,30,255))
fr(sheet,ox,oy, 3,6,6,9, (0,160,70,120))
fr(sheet,ox,oy, 9,6,12,10, (180,100,20,200))
fr(sheet,ox,oy, 10,10,11,11, (180,100,20,200))

# 4: Filing cabinet
ox,oy = sp(4,0)
fr(sheet,ox,oy, 3,2,12,13, (35,35,45,255))
for dy in [3,6,9]:
    fr(sheet,ox,oy, 4,dy,11,dy+2, (50,50,65,255))
    fr(sheet,ox,oy, 7,dy+1,8,dy+1, (200,180,100,255))

# 5: Medical gurney (top-down)
ox,oy = sp(5,0)
fr(sheet,ox,oy, 2,3,13,12, (200,200,205,255))
fr(sheet,ox,oy, 3,4,12,11, (220,220,225,255))
fr(sheet,ox,oy, 3,4,12,5, (200,210,200,255))
fr(sheet,ox,oy, 5,7,8,9, (180,40,40,120))

# 6: Biohazard drum
ox,oy = sp(6,0)
fr(sheet,ox,oy, 3,2,12,13, (80,20,20,255))
fr(sheet,ox,oy, 3,2,12,4, (60,15,15,255))
fr(sheet,ox,oy, 3,11,12,13, (60,15,15,255))
fr(sheet,ox,oy, 7,6,8,9, (200,40,40,255))
fr(sheet,ox,oy, 5,5,6,6, (200,40,40,255))
fr(sheet,ox,oy, 9,5,10,6, (200,40,40,255))
fr(sheet,ox,oy, 6,9,9,10, (200,40,40,255))

# 7: Dual monitor console
ox,oy = sp(7,0)
fr(sheet,ox,oy, 1,3,14,13, (25,28,35,255))
fr(sheet,ox,oy, 2,4,7,10, (0,140,220,255))
fr(sheet,ox,oy, 8,4,13,10, (0,200,80,255))
fr(sheet,ox,oy, 3,5,6,9, (0,60,120,255))
fr(sheet,ox,oy, 9,5,12,9, (0,80,30,255))
fr(sheet,ox,oy, 4,11,11,12, (40,45,55,255))

# ── ROW 1: Furniture ─────────────────────────────────────────────────────

# 8: Chair (overhead)
ox,oy = sp(0,1)
fr(sheet,ox,oy, 4,1,11,4, (80,60,50,255))
fr(sheet,ox,oy, 4,4,11,11, (100,75,60,255))
fr(sheet,ox,oy, 4,11,6,13, (60,45,35,255))
fr(sheet,ox,oy, 9,11,11,13, (60,45,35,255))
fr(sheet,ox,oy, 4,1,6,4, (60,45,35,255))
fr(sheet,ox,oy, 9,1,11,4, (60,45,35,255))

# 9: Round table
ox,oy = sp(1,1)
d = ImageDraw.Draw(sheet)
d.ellipse([ox+3,oy+3,ox+12,oy+12], fill=(120,80,50,255), outline=(80,55,35,255))
d.ellipse([ox+6,oy+6,ox+9,oy+9], fill=(100,65,40,255))

# 10: Rectangular dining table
ox,oy = sp(2,1)
fr(sheet,ox,oy, 2,4,13,11, (130,90,55,255))
fr(sheet,ox,oy, 2,4,13,5, (160,120,80,255))
fr(sheet,ox,oy, 3,6,4,9, (220,210,200,200))
fr(sheet,ox,oy, 11,6,12,9, (220,210,200,200))

# 11: Bench
ox,oy = sp(3,1)
fr(sheet,ox,oy, 2,6,13,9, (100,75,55,255))
fr(sheet,ox,oy, 2,6,13,7, (130,100,75,255))
fr(sheet,ox,oy, 3,9,5,11, (75,55,40,255))
fr(sheet,ox,oy, 10,9,12,11, (75,55,40,255))

# 12: Metal locker
ox,oy = sp(4,1)
fr(sheet,ox,oy, 4,1,11,14, (55,60,70,255))
fr(sheet,ox,oy, 5,2,10,13, (45,50,60,255))
fr(sheet,ox,oy, 7,4,8,5, (180,180,180,255))
fr(sheet,ox,oy, 7,9,8,10, (180,180,180,255))

# 13: Rubble pile
ox,oy = sp(5,1)
for x1,y1,x2,y2 in [(2,4,4,7),(6,3,9,6),(10,5,13,8),(3,8,7,11),(8,8,12,12)]:
    fr(sheet,ox,oy, x1,y1,x2,y2, (70,65,60,255))
for x1,y1,x2,y2 in [(2,4,3,5),(7,4,8,5),(11,5,12,6)]:
    fr(sheet,ox,oy, x1,y1,x2,y2, (90,85,80,255))

# 14: Wall light strip (rectangular — NOT a circle, avoids confusion with enemy tokens)
ox,oy = sp(6,1)
fr(sheet,ox,oy, 3,4,12,11, (45,20,20,255))   # housing
fr(sheet,ox,oy, 4,5,11,10, (30,12,12,255))   # recess
fr(sheet,ox,oy, 5,6,10,9, (190,35,35,200))   # glow bar
fr(sheet,ox,oy, 6,7,9,8, (255,70,70,255))    # bright center strip
fr(sheet,ox,oy, 3,11,5,12, (40,18,18,255))   # left bracket
fr(sheet,ox,oy, 10,11,12,12, (40,18,18,255)) # right bracket

# 15: Floor vent
ox,oy = sp(7,1)
fr(sheet,ox,oy, 2,2,13,13, (50,50,60,255))
for gy in [3,5,7,9,11]:
    fr(sheet,ox,oy, 3,gy,12,gy, (30,30,40,255))

# ── ROW 2: Train Station ──────────────────────────────────────────────────

# 16: Train seats (two seats side by side)
ox,oy = sp(0,2)
for sx in [2,9]:
    fr(sheet,ox,oy, sx,2,sx+4,5, (40,50,80,255))
    fr(sheet,ox,oy, sx,5,sx+4,10, (50,65,100,255))
    fr(sheet,ox,oy, sx,10,sx+1,13, (30,35,55,255))
    fr(sheet,ox,oy, sx+3,10,sx+4,13, (30,35,55,255))

# 17: Overhead handrail
ox,oy = sp(1,2)
fr(sheet,ox,oy, 1,6,14,7, (140,140,160,255))
for hx in [3,7,11]:
    fr(sheet,ox,oy, hx,4,hx+1,9, (120,120,140,255))
    fr(sheet,ox,oy, hx-1,3,hx+2,4, (160,160,180,255))

# 18: Platform bench (steel)
ox,oy = sp(2,2)
fr(sheet,ox,oy, 1,5,14,8, (90,95,100,255))
fr(sheet,ox,oy, 1,5,14,6, (130,140,150,255))
fr(sheet,ox,oy, 1,8,2,11, (70,75,80,255))
fr(sheet,ox,oy, 13,8,14,11, (70,75,80,255))

# 19: Info board
ox,oy = sp(3,2)
fr(sheet,ox,oy, 2,3,13,11, (20,40,80,255))
fr(sheet,ox,oy, 3,4,12,10, (0,60,120,255))
fr(sheet,ox,oy, 4,5,11,6, (255,255,255,200))
fr(sheet,ox,oy, 4,7,8,8, (255,255,255,150))
fr(sheet,ox,oy, 7,11,8,14, (40,45,50,255))

# 20: Train door frame
ox,oy = sp(4,2)
fr(sheet,ox,oy, 1,1,14,14, (35,40,50,255))
fr(sheet,ox,oy, 3,2,12,13, (15,20,30,255))
fr(sheet,ox,oy, 7,5,8,10, (100,120,140,200))
fr(sheet,ox,oy, 2,2,3,13, (50,60,75,255))
fr(sheet,ox,oy, 12,2,13,13, (50,60,75,255))

# 21: Luggage rack
ox,oy = sp(5,2)
fr(sheet,ox,oy, 1,3,14,5, (80,85,90,255))
fr(sheet,ox,oy, 1,3,14,4, (120,130,140,255))
for bx in [2,5,8,11]:
    fr(sheet,ox,oy, bx,5,bx+1,8, (60,65,70,255))
fr(sheet,ox,oy, 1,8,14,10, (65,70,75,255))

# 22: Umbrella Corp plaque
ox,oy = sp(6,2)
fr(sheet,ox,oy, 3,3,12,12, (180,20,20,255))
fr(sheet,ox,oy, 4,4,11,11, (200,30,30,255))
fr(sheet,ox,oy, 5,5,6,9, (255,255,255,255))
fr(sheet,ox,oy, 9,5,10,9, (255,255,255,255))
fr(sheet,ox,oy, 5,9,10,10, (255,255,255,255))
fr(sheet,ox,oy, 7,7,8,9, (255,255,255,255))

# 23: Security camera
ox,oy = sp(7,2)
fr(sheet,ox,oy, 6,1,9,4, (60,60,70,255))
fr(sheet,ox,oy, 4,4,11,9, (50,50,60,255))
d3 = ImageDraw.Draw(sheet)
d3.ellipse([ox+5,oy+5,ox+10,oy+8], fill=(20,20,25,255), outline=(0,150,220,255))
d3.ellipse([ox+7,oy+6,ox+8,oy+7], fill=(0,80,180,255))

# ── ROW 3: Hive Special ───────────────────────────────────────────────────

# 24: Keypad panel
ox,oy = sp(0,3)
fr(sheet,ox,oy, 4,2,11,13, (30,35,45,255))
fr(sheet,ox,oy, 5,3,10,7, (0,150,80,200))
for bx,by in [(5,8),(7,8),(9,8),(5,10),(7,10),(9,10),(5,12),(7,12),(9,12)]:
    fr(sheet,ox,oy, bx,by,bx+1,by+1, (80,100,120,255))

# 25: Blood pool
ox,oy = sp(1,3)
d4 = ImageDraw.Draw(sheet)
d4.ellipse([ox+3,oy+5,ox+12,oy+11], fill=(120,10,10,200))
d4.ellipse([ox+5,oy+4,ox+10,oy+8], fill=(150,15,15,220))
d4.ellipse([ox+7,oy+3,ox+9,oy+6], fill=(180,20,20,240))

# 26: Zombie corpse (lying flat/horizontal — clearly dead, not an upright character)
ox,oy = sp(2,3)
fr(sheet,ox,oy, 1,6,4,9, (150,120,100,255))   # head (left side)
fr(sheet,ox,oy, 4,6,13,9, (80,70,60,255))     # torso (horizontal)
fr(sheet,ox,oy, 13,6,15,8, (70,60,50,255))    # legs
fr(sheet,ox,oy, 5,4,7,6, (70,60,50,255))      # arm (up)
fr(sheet,ox,oy, 8,9,10,12, (70,60,50,255))    # arm (down)
fr(sheet,ox,oy, 1,7,14,9, (100,10,10,100))    # blood pool under body

# 27: Cryogenic pod
ox,oy = sp(3,3)
d5 = ImageDraw.Draw(sheet)
d5.ellipse([ox+3,oy+2,ox+12,oy+13], fill=(0,80,120,200), outline=(0,180,220,255))
d5.ellipse([ox+5,oy+4,ox+10,oy+11], fill=(0,40,80,220))
fr(sheet,ox,oy, 7,5,8,10, (180,200,220,180))
fr(sheet,ox,oy, 5,7,10,8, (180,200,220,160))

# 28: Red Queen eye
ox,oy = sp(4,3)
fr(sheet,ox,oy, 1,1,14,14, (15,5,5,255))
d6 = ImageDraw.Draw(sheet)
d6.ellipse([ox+3,oy+3,ox+12,oy+12], fill=(80,0,0,255), outline=(200,0,0,255))
d6.ellipse([ox+5,oy+5,ox+10,oy+10], fill=(180,10,10,255))
d6.ellipse([ox+6,oy+6,ox+9,oy+9], fill=(255,30,30,255))
d6.ellipse([ox+7,oy+7,ox+8,oy+8], fill=(255,255,255,255))

# 29: T-virus vial
ox,oy = sp(5,3)
fr(sheet,ox,oy, 6,1,9,2, (100,80,70,255))
fr(sheet,ox,oy, 5,2,10,12, (180,20,20,200))
fr(sheet,ox,oy, 6,3,9,11, (220,40,40,255))
fr(sheet,ox,oy, 7,4,8,10, (255,80,80,255))
fr(sheet,ox,oy, 5,12,10,13, (80,60,55,255))

# 30: Fuse/electrical panel
ox,oy = sp(6,3)
fr(sheet,ox,oy, 3,2,12,13, (50,50,45,255))
fr(sheet,ox,oy, 4,3,11,12, (35,35,30,255))
for cy in [4,6,8,10]:
    fr(sheet,ox,oy, 5,cy,10,cy+1, (200,180,50,150))
fr(sheet,ox,oy, 7,4,8,11, (255,200,0,200))

# 31: Toxic barrel (green)
ox,oy = sp(7,3)
fr(sheet,ox,oy, 3,2,12,13, (40,70,25,255))
fr(sheet,ox,oy, 3,2,12,4, (30,55,20,255))
fr(sheet,ox,oy, 3,5,12,6, (30,55,20,255))
fr(sheet,ox,oy, 3,10,12,11, (30,55,20,255))
fr(sheet,ox,oy, 6,7,9,9, (80,200,30,255))
d7 = ImageDraw.Draw(sheet)
d7.ellipse([ox+5,oy+6,ox+10,oy+10], fill=(0,0,0,0))
fr(sheet,ox,oy, 6,7,9,9, (60,180,20,200))

# ── ROW 4: Floor tiles ────────────────────────────────────────────────────

def make_floor(col, row, base, detail, style='grid'):
    ox,oy = sp(col, row)
    fr(sheet,ox,oy, 0,0,15,15, base)
    da = (*detail[:3], 60)
    if style == 'grid':
        for gx in [4,8,12]: fr(sheet,ox,oy, gx,0,gx,15, da)
        for gy in [4,8,12]: fr(sheet,ox,oy, 0,gy,15,gy, da)
    elif style == 'crack':
        for cx,cy in [(3,2),(5,7),(9,4),(11,10),(2,12)]:
            fr(sheet,ox,oy, cx,cy,cx+2,cy, (*detail[:3],90))
    elif style == 'dots':
        for gx in [3,7,11]:
            for gy in [3,7,11]:
                fr(sheet,ox,oy, gx,gy,gx+1,gy+1, (*detail[:3],110))
    elif style == 'stripe':
        for gx in [2,6,10,14]: fr(sheet,ox,oy, gx,0,gx,15, (*detail[:3],45))
    elif style == 'hex':
        for gx in [0,4,8,12]:
            for gy in [0,4,8,12]:
                fr(sheet,ox,oy, gx,gy,gx+1,gy+1, (*detail[:3],80))
    elif style == 'diamond':
        dd = ImageDraw.Draw(sheet)
        for gx in [4,12]:
            for gy in [4,12]:
                dd.polygon([ox+gx,oy+gy-2,ox+gx+2,oy+gy,ox+gx,oy+gy+2,ox+gx-2,oy+gy],
                           fill=(*detail[:3],70))
    # darken corners
    for cx,cy in [(0,0),(15,0),(0,15),(15,15)]:
        sheet.putpixel((ox+cx,oy+cy), (*detail[:3],100))

make_floor(0,4, (18,22,28,255), (40,55,80,255), 'grid')     # corridor (blue-grey)
make_floor(1,4, (20,18,14,255), (45,40,30,255), 'crack')    # tunnels (worn concrete)
make_floor(2,4, (16,20,14,255), (35,55,30,255), 'hex')      # lab green hex
make_floor(3,4, (22,16,14,255), (50,30,25,255), 'dots')     # earth/dirt
make_floor(4,4, (12,10,18,255), (50,35,80,255), 'diamond')  # Red Queen (dark purple)
make_floor(5,4, (18,24,28,255), (40,70,80,255), 'stripe')   # train platform (steel)
make_floor(6,4, (24,20,14,255), (60,50,32,255), 'grid')     # dining (warm stone)
make_floor(7,4, (12,18,16,255), (25,50,42,255), 'hex')      # deep lab (teal)

out = 'C:/laragon/www/terror-infinity-rpg/assets/sprites/hive_props.png'
sheet.save(out)
print(f"Saved {out} — {W}x{H} px, {COLS*ROWS} sprites at 16x16")
