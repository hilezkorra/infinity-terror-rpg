import json

path = r'C:\laragon\www\terror-infinity-rpg\data\game.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    g = json.load(f)

# Give the guide a starting location
g['guide']['location'] = 'hive-train'

# Inject canvas_map into world_map
g['world_map']['canvas_map'] = {
    "tile_px": 16,
    "grid_w":  33,
    "grid_h":  22,
    "rooms": [
        {"id":"hive-train",          "x":0,  "y":8,  "w":5, "h":5, "label":"Hive Train",         "type":"train"},
        {"id":"entrance-hall",       "x":6,  "y":5,  "w":9, "h":10,"label":"Entrance Hall",       "type":"floor"},
        {"id":"main-corridor",       "x":16, "y":9,  "w":9, "h":4, "label":"Main Corridor",       "type":"corridor"},
        {"id":"dining-hall",         "x":17, "y":1,  "w":8, "h":8, "label":"Staff Dining Hall",   "type":"dining"},
        {"id":"lab-level",           "x":17, "y":14, "w":9, "h":6, "label":"Laboratory Level",    "type":"lab"},
        {"id":"maintenance-tunnels", "x":10, "y":15, "w":6, "h":5, "label":"Maintenance Tunnels", "type":"tunnels"},
        {"id":"red-queen-chamber",   "x":26, "y":8,  "w":7, "h":7, "label":"Red Queen Chamber",   "type":"red_queen"}
    ],
    "connections": [
        {"from":"hive-train",          "to":"entrance-hall"},
        {"from":"entrance-hall",       "to":"main-corridor"},
        {"from":"main-corridor",       "to":"dining-hall"},
        {"from":"main-corridor",       "to":"lab-level"},
        {"from":"maintenance-tunnels", "to":"lab-level"},
        {"from":"main-corridor",       "to":"red-queen-chamber"}
    ]
}

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(g, f, ensure_ascii=False, indent=2)
print('Done. Guide location:', g['guide']['location'])
print('canvas_map rooms:', len(g['world_map']['canvas_map']['rooms']))
