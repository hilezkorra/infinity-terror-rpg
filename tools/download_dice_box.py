"""Download @3d-dice/dice-box@1.1.4 assets for local hosting.
Run from the project root: python tools/download_dice_box.py
Places files under assets/dice-box/ so workers stay same-origin.
"""
import urllib.request
import os
import time
import sys

BASE = 'https://cdn.jsdelivr.net/npm/@3d-dice/dice-box@1.1.4'
OUT  = 'assets/dice-box'

FILES = [
    # Main library + workers (must be same-origin as index.html)
    ('dist/dice-box.es.js',           'dice-box.es.js'),
    ('dist/world.offscreen.js',       'world.offscreen.js'),
    ('dist/world.onscreen.js',        'world.onscreen.js'),
    ('dist/world.none.js',            'world.none.js'),
    ('dist/Dice.js',                  'Dice.js'),
    # Physics WASM
    ('dist/assets/ammo/ammo.wasm.wasm', 'assets/ammo/ammo.wasm.wasm'),
    # Default theme textures
    ('dist/assets/themes/default/theme.config.json', 'assets/themes/default/theme.config.json'),
    ('dist/assets/themes/default/default.json',      'assets/themes/default/default.json'),
    ('dist/assets/themes/default/diffuse-dark.png',  'assets/themes/default/diffuse-dark.png'),
    ('dist/assets/themes/default/diffuse-light.png', 'assets/themes/default/diffuse-light.png'),
    ('dist/assets/themes/default/normal.png',        'assets/themes/default/normal.png'),
    ('dist/assets/themes/default/specular.jpg',      'assets/themes/default/specular.jpg'),
]

def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, 'wb') as f:
        data = r.read()
        f.write(data)
    return len(data)

total = 0
for src_path, local_path in FILES:
    url  = f'{BASE}/{src_path}'
    dest = os.path.join(OUT, local_path)
    if os.path.exists(dest):
        size = os.path.getsize(dest)
        print(f'  skip  {local_path} ({size//1024}KB already exists)')
        continue
    try:
        size = download(url, dest)
        total += size
        print(f'  ok    {local_path} ({size//1024}KB)')
        time.sleep(0.15)
    except Exception as e:
        print(f'  FAIL  {local_path}: {e}', file=sys.stderr)

print(f'\nDone. {total//1024}KB downloaded to {OUT}/')
