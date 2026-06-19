"""
Download free character portraits and monster sprites for Terror Infinity RPG.

PORTRAIT SOURCES (free, no attribution required or CC0/CC-BY):
  Characters : https://opengameart.org/content/painterly-spell-icons  (placeholder)
  VN sprites : https://sutemo.itch.io/female-character  (free tier)
               https://beamedbits.itch.io/free-vn-characters

  For Resident Evil monsters specifically:
    - Zombie sprites: https://opengameart.org/content/zombie-sprites
    - Generic horror: https://opengameart.org/content/horror-tiles

USAGE:
  1. Download sprite sheets or individual PNGs from the URLs above.
  2. Drop them into  assets/portraits/  as  <slug>.png
     where slug = character name lowercased with spaces → hyphens.
     Examples:
       Igor Pundzin  →  igor-pundzin.png
       Vera Kessler  →  vera-kessler.png
       Yuki Tanaka   →  yuki-tanaka.png
       Zombie        →  zombie.png
       Licker        →  licker.png
  3. The game checks assets/portraits/<slug>.png first;
     if missing it falls back to DiceBear adventurer API.

Below is an automated downloader for DiceBear SVG portraits as PNG proxies
so you have something decent right away.  Real PNGs in the folder will
always override these.

Run from the project root:
    python tools/download_portraits.py
"""

import urllib.request
import os
import json

OUT = 'assets/portraits'
os.makedirs(OUT, exist_ok=True)

# Characters defined in game.json — update as roster grows
CHARACTERS = [
    ('igor-pundzin',  'player'),
    ('vera-kessler',  'ally'),
    ('yuki-tanaka',   'ally'),
]

# Enemy / monster types
ENEMIES = [
    ('zombie',   'enemy'),
    ('licker',   'enemy'),
    ('hunter',   'enemy'),
    ('crimson-head', 'enemy'),
    ('ghost',    'enemy'),
    ('cerberus', 'enemy'),
    ('neptune',  'enemy'),
]

def dicebear_png_url(slug, role):
    """DiceBear PNG endpoint — 200px, good quality for portraits."""
    enc = urllib.request.quote(slug.replace('-', ' ').title())
    if role == 'enemy':
        return (f'https://api.dicebear.com/9.x/thumbs/png'
                f'?seed={enc}&size=200&backgroundColor=1a0a08&shapeColor=8b0000,5c0000,3d0000')
    else:
        return (f'https://api.dicebear.com/9.x/adventurer/png'
                f'?seed={enc}&size=200&backgroundColor=0d1117&radius=6')

def download_png(url, dest):
    """Download a PNG file, skip if already exists."""
    if os.path.exists(dest):
        print(f'  skip  {dest}')
        return True
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r, open(dest, 'wb') as f:
            data = r.read()
            f.write(data)
        print(f'  ok    {dest}  ({len(data)//1024}KB)')
        return True
    except Exception as e:
        print(f'  FAIL  {dest}: {e}')
        return False

import time

print('Downloading DiceBear PNG portraits as placeholder avatars...')
print('(Drop real PNG files into assets/portraits/ to override these)')
print()

for slug, role in CHARACTERS + ENEMIES:
    url  = dicebear_png_url(slug, role)
    dest = os.path.join(OUT, slug + '.png')
    download_png(url, dest)
    time.sleep(0.2)  # be polite to the API

print()
print('Done. Files saved to', OUT)
print()
print('To use real portraits:')
print('  1. Find free VN sprites on itch.io or opengameart.org')
print('  2. Save as assets/portraits/<name-slug>.png')
print('  3. The game will automatically use them instead of DiceBear')
print()
print('Suggested free packs:')
print('  https://sutemo.itch.io/female-character  (free VN female)')
print('  https://beamedbits.itch.io/free-vn-characters  (diverse cast)')
print('  https://opengameart.org/content/zombie-sprites  (zombie)')
