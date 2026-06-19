import json, random

path = r'C:\laragon\www\terror-infinity-rpg\data\game.json'
tg_path = r'C:\laragon\www\terror-infinity-rpg\system\team-gen.json'
tr_path = r'C:\laragon\www\terror-infinity-rpg\system\personality-traits.json'

with open(path,   'r', encoding='utf-8-sig') as f: g  = json.load(f)
with open(tg_path,'r', encoding='utf-8-sig') as f: tg = json.load(f)
with open(tr_path,'r', encoding='utf-8-sig') as f: tr_raw = json.load(f)
tr = tr_raw['traits'] if isinstance(tr_raw, dict) else tr_raw

def pick_traits(traits, n=5):
    positives = [t for t in traits if t.get('type') == 'pos']
    negatives = [t for t in traits if t.get('type') == 'neg']
    pos_count = random.randint(3, min(4, len(positives)))
    neg_count = n - pos_count
    picked = random.sample(positives, pos_count) + random.sample(negatives, neg_count)
    return [{'name': t['name'], 'type': t['type'], 'desc': t['desc']} for t in picked]

# Japanese nationality data
jp = next(n for n in tg['nationalities'] if n['country'] == 'Japanese')

age = random.randint(22, 35)
occupation = random.choice(tg['occupations'])

# Physical characteristics
hair = random.choices([c['c'] for c in jp['hair_colors']], weights=[c['w'] for c in jp['hair_colors']])[0]
eye  = random.choices([c['c'] for c in jp['eye_colors']],  weights=[c['w'] for c in jp['eye_colors']])[0]
skin = random.choices([t['t'] for t in jp['skin_tones']],  weights=[t['w'] for t in jp['skin_tones']])[0]
build = random.choice([b['label'] if isinstance(b, dict) else b for b in tg['builds']])
hf = jp['height_female']
height = random.randint(hf[0], hf[1]) if isinstance(hf, list) else random.randint(hf['min'], hf['max'])
orientation = random.choices(
    [o['label'] for o in tg['sexual_orientations']],
    weights=[o['weight'] for o in tg['sexual_orientations']]
)[0]
city = random.choice(jp.get('cities', ['Tokyo']))

# Alignment
alignment = random.choices(tg['alignments'], weights=[a['weight'] for a in tg['alignments']])[0]
stance = random.choice(alignment['attitudes'])

# Stats
occ_stats = {}
for stat in ['str', 'agi', 'end', 'int', 'lck', 'psy']:
    r = occupation.get(stat, [7, 13])
    occ_stats[stat] = random.randint(r[0], r[1])

yuki = {
    "name": "Yuki Tanaka",
    "gender": "female",
    "age": age,
    "nationality": "Japanese",
    "city_of_origin": city,
    "occupation": occupation['label'],
    "location": "hive-train",
    "alive": True,
    "hp": 100,
    "hp_max": 100,
    "team_stance": stance,
    "alignment": alignment['label'],
    "stats": occ_stats,
    "skills": occupation.get('skills', []),
    "personality": pick_traits(tr),
    "physical": {
        "height_cm": height,
        "hair_color": hair,
        "eye_color": eye,
        "skin_tone": skin,
        "build": build,
        "sexual_orientation": orientation
    }
}

g['team']['members'] = [yuki]

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(g, f, ensure_ascii=False, indent=2)
print(f"Added Yuki Tanaka — {yuki['occupation']}, {city}, stance={stance}")
print(f"Traits: {[t['name'] for t in yuki['personality']]}")
