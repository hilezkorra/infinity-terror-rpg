"""Restructure canvas_map to multi-floor layout for The Hive."""
import json, sys

path = 'data/game.json'
with open(path, encoding='utf-8-sig') as f:
    d = json.load(f)

wm = d.setdefault('world_map', {})

floors = {
    "B1": {
        "label": "Level B1 — Access & Transit",
        "desc": "The entry level of the Hive. The Alexi-500 train terminates here. Security checkpoint leads deeper into the facility.",
        "grid_w": 42, "grid_h": 28, "tile_px": 8,
        "rooms": [
            {
                "id": "hive-train", "label": "Train Platform",
                "type": "train_station", "indoor": True,
                "x": 0, "y": 9, "w": 10, "h": 10,
                "desc": "Underground platform serving the Alexi-500 rapid transit. Emergency lighting only — the T-virus outbreak triggered automatic lockdown."
            },
            {
                "id": "entrance-hall", "label": "Entrance Atrium",
                "type": "floor", "indoor": True,
                "x": 12, "y": 2, "w": 14, "h": 24,
                "desc": "The main atrium of the Hive. Corporate art and Umbrella insignia line the walls. Blood smears trail toward the lower corridor."
            },
            {
                "id": "security-checkpoint", "label": "Security Gate",
                "type": "checkpoint", "indoor": True,
                "x": 28, "y": 9, "w": 12, "h": 8,
                "desc": "Biometric security checkpoint. Blast doors separate this level from B2 operations. Red emergency lights pulse overhead."
            }
        ],
        "connections": [
            {"from": "hive-train",       "to": "entrance-hall",      "door": True},
            {"from": "entrance-hall",    "to": "security-checkpoint", "door": True}
        ]
    },
    "B2": {
        "label": "Level B2 — Operations",
        "desc": "Primary operations level. Contains the dining hall, medical wing, armory, and maintenance infrastructure.",
        "grid_w": 54, "grid_h": 34, "tile_px": 8,
        "rooms": [
            {
                "id": "dining-hall", "label": "Cafeteria",
                "type": "dining", "indoor": True,
                "x": 2, "y": 2, "w": 16, "h": 13,
                "desc": "Staff cafeteria. Tables are overturned. Half-eaten food trays litter the floor. Something happened here fast."
            },
            {
                "id": "medical-bay", "label": "Medical Bay",
                "type": "medical", "indoor": True,
                "x": 20, "y": 2, "w": 14, "h": 13,
                "desc": "Umbrella's medical facility for Hive personnel. Gurneys are bloodied. Several specimen jars have been shattered."
            },
            {
                "id": "main-corridor", "label": "Main Corridor",
                "type": "corridor", "indoor": True,
                "x": 2, "y": 17, "w": 32, "h": 6,
                "desc": "The central artery of the Hive's operations level. Emergency lighting is intact. Claw marks on the walls."
            },
            {
                "id": "maintenance-tunnels", "label": "Maintenance Tunnels",
                "type": "tunnels", "indoor": True,
                "x": 2, "y": 25, "w": 16, "h": 8,
                "desc": "Utility tunnels beneath the operations floor. Pipe networks and ventilation shafts. Easy to get lost — or cornered."
            },
            {
                "id": "armory", "label": "Armory",
                "type": "armory", "indoor": True,
                "x": 36, "y": 17, "w": 16, "h": 10,
                "desc": "Security armory. Weapons racks have been raided. A few rifles remain. Ammo crates are stacked against the far wall."
            }
        ],
        "connections": [
            {"from": "main-corridor",     "to": "dining-hall",          "door": True},
            {"from": "main-corridor",     "to": "medical-bay",          "door": True},
            {"from": "main-corridor",     "to": "maintenance-tunnels",  "door": False},
            {"from": "main-corridor",     "to": "armory",               "door": True},
            {"from": "maintenance-tunnels","to": "armory",              "door": False}
        ]
    },
    "B3": {
        "label": "Level B3 — Restricted Research",
        "desc": "The deepest and most classified section of the Hive. The T-virus was engineered here. The Red Queen AI governs all access.",
        "grid_w": 50, "grid_h": 32, "tile_px": 8,
        "rooms": [
            {
                "id": "lab-level", "label": "Research Labs",
                "type": "lab", "indoor": True,
                "x": 2, "y": 8, "w": 20, "h": 16,
                "desc": "Umbrella's primary T-virus research laboratories. Containment has failed. Overturned specimen racks, shattered glass. The smell is overwhelming."
            },
            {
                "id": "containment-cells", "label": "Containment Block",
                "type": "containment", "indoor": True,
                "x": 2, "y": 0, "w": 20, "h": 7,
                "desc": "Specimen containment cells. All cells show signs of forced breach from the inside. Reinforced glass is shattered outward."
            },
            {
                "id": "executive-suites", "label": "Cryo Storage",
                "type": "cryogenic", "indoor": True,
                "x": 24, "y": 0, "w": 12, "h": 20,
                "desc": "Cryogenic storage for senior Umbrella personnel. Pods are still operational. Several show occupants in stasis — alive, for now."
            },
            {
                "id": "red-queen-chamber", "label": "Red Queen Core",
                "type": "red_queen", "indoor": True,
                "x": 36, "y": 10, "w": 12, "h": 12,
                "desc": "The processing core of the Red Queen AI. Holographic projectors line the walls. Her voice echoes through the chamber: 'You are all going to die down here.'"
            }
        ],
        "connections": [
            {"from": "lab-level",         "to": "containment-cells",  "door": True},
            {"from": "lab-level",         "to": "executive-suites",   "door": True},
            {"from": "lab-level",         "to": "red-queen-chamber",  "door": True},
            {"from": "containment-cells", "to": "executive-suites",   "door": False}
        ]
    }
}

# Preserve active floor if already set
existing = wm.get('canvas_map', {})
active = existing.get('active_floor', 'B1')

wm['canvas_map'] = {
    "active_floor": active,
    "floors": floors
}

# Update character/NPC locations to valid room IDs
valid_ids = set()
for fl in floors.values():
    for r in fl['rooms']:
        valid_ids.add(r['id'])

for key in ['character', 'guide']:
    obj = d.get(key)
    if obj and obj.get('location') and obj['location'] not in valid_ids:
        # Map old location to new
        old = obj['location']
        mapping = {
            'main-corridor': 'main-corridor',
            'entrance-hall': 'entrance-hall',
            'hive-train': 'hive-train',
            'dining-hall': 'dining-hall',
            'lab-level': 'lab-level',
            'red-queen-chamber': 'red-queen-chamber',
        }
        obj['location'] = mapping.get(old, 'entrance-hall')

for m in (d.get('team') or {}).get('members', []):
    if m.get('location') and m['location'] not in valid_ids:
        m['location'] = 'main-corridor'

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print('game.json updated — multi-floor canvas_map written.')
print(f'Floors: {list(floors.keys())}')
for fid, fl in floors.items():
    print(f'  {fid}: {[r["id"] for r in fl["rooms"]]}')
