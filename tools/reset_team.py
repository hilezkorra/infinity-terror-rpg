import json

path = r'C:\laragon\www\terror-infinity-rpg\data\game.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    g = json.load(f)

members = g.get('team', {}).get('members', [])

# Find Yuki Tanaka
yuki = next((m for m in members if 'yuki' in m.get('name','').lower() or 'tanaka' in m.get('name','').lower()), None)

if yuki:
    # Reset memories / relationship data
    yuki.pop('memory', None)
    yuki.pop('memories', None)
    yuki.pop('relationship', None)
    yuki.pop('notes', None)
    yuki['location'] = 'hive-train'
    yuki.pop('sublocation', None)
    yuki['alive'] = True
    g['team']['members'] = [yuki]
    print(f"Kept: {yuki['name']} | location: {yuki['location']}")
else:
    g['team']['members'] = []
    print("WARNING: Yuki Tanaka not found. Team cleared.")

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(g, f, ensure_ascii=False, indent=2)
print(f"Team now has {len(g['team']['members'])} member(s).")
