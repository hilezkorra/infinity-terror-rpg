#!/usr/bin/env python3
"""
Terror Infinity RPG — Portrait crawler
Reads every character from game.json, then downloads a DiceBear PNG
for any that don't already have a local file in assets/portraits/.

Styles:
  - allies / players / neutral  → adventurer  (illustrated human faces)
  - enemies / hostile           → thumbs       (darker monster-ish style)
  - named bosses (tyrant, nemesis, etc.) → notionists (creepy/abstract)

Run from any directory — paths are resolved relative to this script.
"""

import json, re, os, time, sys
import urllib.request, urllib.parse

# ── Paths ────────────────────────────────────────────────────────────
ROOT        = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
GAME_JSON   = os.path.join(ROOT, 'data', 'game.json')
PORTRAITS   = os.path.join(ROOT, 'assets', 'portraits')

# ── Style rules ──────────────────────────────────────────────────────
# slug fragments that should use the 'notionists' horror style
BOSS_SLUGS = {'tyrant', 'nemesis', 'cerberus', 'neptune', 'hunter', 'phantom', 'crimson'}

def _style_for(slug, role):
    if any(b in slug for b in BOSS_SLUGS):
        return 'notionists', '&backgroundColor=120808&size=400'
    if role in ('enemy', 'hostile'):
        return 'thumbs', '&backgroundColor=1a0a08&shapeColor=8b0000,5c0000,3d0000&size=400'
    return 'adventurer', '&backgroundColor=0d1117&radius=6&size=400'

def dicebear_url(name, slug, role):
    seed  = urllib.parse.quote(name.strip())
    style, extra = _style_for(slug, role)
    return f'https://api.dicebear.com/9.x/{style}/png?seed={seed}{extra}'

# ── Slug helper (matches JS _diceBearUrl logic) ───────────────────────
def slugify(name):
    s = re.sub(r'[^a-z0-9-]', '', re.sub(r'\s+', '-', (name or '').strip().lower()))
    return s or 'unknown'

# ── Collect all characters from game.json ───────────────────────────
def collect_chars(g):
    chars = {}

    def add(name, role):
        if not name:
            return
        slug = slugify(name)
        if slug not in chars:
            chars[slug] = {'name': name, 'role': role, 'slug': slug}

    # Main PC
    ch = g.get('character') or {}
    add(ch.get('name'), 'player')

    # Active combat roster
    for c in (g.get('combat') or {}).get('combatants', []):
        add(c.get('name'), c.get('role', 'enemy'))

    # Team — can be {name, continent, members:[...]} or a plain list
    team = g.get('team') or []
    team_members = team.get('members', []) if isinstance(team, dict) else team
    for m in team_members:
        if isinstance(m, dict):
            add(m.get('name'), m.get('role', 'ally'))

    # NPCs dict
    for _k, v in ((g.get('npcs') or {}).items()):
        if isinstance(v, dict):
            add(v.get('name'), v.get('role', 'neutral'))

    # Guide
    guide = g.get('guide') or {}
    if isinstance(guide, dict):
        add(guide.get('name'), 'ally')

    return chars

# ── Download helper ──────────────────────────────────────────────────
HEADERS = {'User-Agent': 'TerrorInfinity-PortraitCrawler/1.0'}

def download(url, dest, retries=3):
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if len(data) < 500:
                raise ValueError(f'suspiciously small response ({len(data)} bytes)')
            with open(dest, 'wb') as f:
                f.write(data)
            return len(data)
        except Exception as e:
            if attempt == retries:
                raise
            print(f'       retry {attempt}/{retries}: {e}')
            time.sleep(1.5 * attempt)

# ── Main ─────────────────────────────────────────────────────────────
def main():
    os.makedirs(PORTRAITS, exist_ok=True)

    with open(GAME_JSON, encoding='utf-8-sig') as f:
        g = json.load(f)

    chars = collect_chars(g)
    print(f'Found {len(chars)} unique characters in game.json\n')

    col_w = max(len(s) for s in chars) + 2
    downloaded = skipped = failed = 0

    for slug in sorted(chars):
        c    = chars[slug]
        dest = os.path.join(PORTRAITS, f'{slug}.png')

        if os.path.exists(dest):
            size = os.path.getsize(dest)
            print(f'  SKIP  {slug:<{col_w}} already exists ({size//1024} KB)')
            skipped += 1
            continue

        url = dicebear_url(c['name'], slug, c['role'])
        print(f'  GET   {slug:<{col_w}} [{c["role"]}]  ', end='', flush=True)
        try:
            kb = download(url, dest) // 1024
            print(f'OK  ({kb} KB)')
            downloaded += 1
            time.sleep(0.4)          # be polite to the DiceBear API
        except Exception as e:
            print(f'FAIL  {e}')
            failed += 1

    print(f'\n{"-"*55}')
    print(f'Downloaded : {downloaded}')
    print(f'Skipped    : {skipped}  (already had local file)')
    print(f'Failed     : {failed}')
    if failed:
        print('Re-run the script to retry failed downloads.')
    else:
        print('All portraits are ready.')

if __name__ == '__main__':
    main()
