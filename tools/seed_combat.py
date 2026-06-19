"""Seed a rich combat structure into game.json.
Builds a sample test encounter from the existing character + first team member.
Set combat.active = True in game.json (or via the UI) to preview the battle screen.
"""
import json

path = 'data/game.json'
with open(path, encoding='utf-8-sig') as f:
    d = json.load(f)

char = d.get('character', {})
team = (d.get('team') or {}).get('members', [])

combatants = []
init = 18

# Player character
if char.get('name'):
    combatants.append({
        "id": "pc_" + char['name'].lower().replace(' ', '_'),
        "name": char['name'],
        "role": "player",
        "hp": char.get('hp', 60),
        "hp_max": char.get('hp_max', 60),
        "mp": char.get('mp', 0),
        "mp_max": char.get('mp_max', 0),
        "status_effects": char.get('status_effects', []),
        "initiative": init
    })
    init -= 4

# First team ally
for m in team[:2]:
    combatants.append({
        "id": "ally_" + m['name'].lower().replace(' ', '_'),
        "name": m['name'],
        "role": "ally",
        "hp": m.get('hp', 72),
        "hp_max": m.get('hp_max', 72),
        "mp": m.get('mp', 0),
        "mp_max": m.get('mp_max', 0),
        "status_effects": m.get('status_effects', []),
        "initiative": init
    })
    init -= 3

# Sample enemies
enemies = [
    {"id": "licker_1",  "name": "Licker",  "role": "enemy", "type": "licker",
     "hp": 80, "hp_max": 120, "mp": 0, "mp_max": 0,
     "status_effects": [], "initiative": init},
    {"id": "zombie_1",  "name": "Zombie",  "role": "enemy", "type": "zombie",
     "hp": 35, "hp_max": 60,  "mp": 0, "mp_max": 0,
     "status_effects": ["bleeding"], "initiative": init - 5},
]

all_combatants = sorted(combatants + enemies, key=lambda x: -x['initiative'])

d['combat'] = {
    "active": False,
    "round": 1,
    "turn_index": 0,
    "location": char.get('location', 'Unknown'),
    "combatants": all_combatants,
    "combat_log": [
        "Combat begins. A Licker drops from the ventilation shaft above.",
        f"Turn order: {', '.join(c['name'] for c in all_combatants)}.",
        f"Round 1 — {all_combatants[0]['name']} acts first."
    ]
}

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print('Combat structure seeded.')
print('Combatants in order:')
for i, c in enumerate(all_combatants):
    print(f"  [{i}] {c['name']} ({c['role']}) — init {c['initiative']}, HP {c['hp']}/{c['hp_max']}")
print("\nSet combat.active = true in game.json to test the battle screen.")
