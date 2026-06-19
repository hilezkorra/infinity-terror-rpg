"""Seed fog-of-war explored[] arrays into canvas_map floors.
Marks rooms currently occupied by any character as explored.
Safe to re-run — only adds missing explored keys."""
import json

path = 'data/game.json'
with open(path, encoding='utf-8-sig') as f:
    d = json.load(f)

# Collect all character locations
locs = set()
for key in ('character', 'guide'):
    obj = d.get(key)
    if obj and obj.get('location'):
        locs.add(obj['location'])
for m in (d.get('team') or {}).get('members', []):
    if m.get('location'):
        locs.add(m['location'])
for npc in (d.get('npcs') or []):
    if npc.get('location'):
        locs.add(npc['location'])

floors = d['world_map']['canvas_map']['floors']
for fid, floor in floors.items():
    room_ids = {r['id'] for r in floor.get('rooms', [])}
    if 'explored' not in floor:
        floor['explored'] = []
    existing = set(floor['explored'])
    # Auto-add currently occupied rooms
    for loc in locs:
        if loc in room_ids and loc not in existing:
            floor['explored'].append(loc)
            existing.add(loc)
    print(f'{fid}: explored = {floor["explored"]}')

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print('Done.')
