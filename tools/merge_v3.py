#!/usr/bin/env python3
"""
Merge script: loads occupation data from JSON chunks and hobbies,
adds them to team-gen.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEAM_GEN = ROOT / 'system' / 'team-gen.json'

with open(TEAM_GEN, 'r', encoding='utf-8') as f:
    data = json.load(f)

existing_ids = {o['id'] for o in data['occupations']}
NEW = []
CNT = {'common':0,'uncommon':0,'rare':0,'very_rare':0,'legendary':0}
SEQ = [0]

def occ_id():
    SEQ[0] += 1
    n = len(data['occupations']) + SEQ[0]
    uid = f"occ-{n:05d}"
    while uid in existing_ids:
        SEQ[0] += 1
        n = len(data['occupations']) + SEQ[0]
        uid = f"occ-{n:05d}"
    return uid

def add_occ(label, ar, ra, tags, st, ag, en, it, lk, ps, skills, desc):
    CNT[ra] += 1
    NEW.append(dict(
        id=occ_id(), label=label, archetype=ar, rarity=ra,
        tags=tags, desc=desc,
        str=st, agi=ag, end=en, int=it, lck=lk, psy=ps,
        skills=skills
    ))

# Load occupation data files
for fname in ['new_occ1.json', 'new_occ2.json', 'new_occ3.json',
              'new_occ4.json', 'new_occ5.json', 'new_occ6.json', 'new_occ7.json']:
    fpath = ROOT / 'tools' / fname
    if not fpath.exists():
        # try temp directory
        fpath = Path(r'C:\Users\CC-Student\AppData\Local\Temp\opencode') / fname
    if fpath.exists():
        with open(fpath, 'r', encoding='utf-8') as f:
            occs = json.load(f)
        for entry in occs:
            add_occ(*entry)
        print(f"Loaded {len(occs)} from {fpath.name}")
    else:
        print(f"NOT FOUND: {fname}")

# Add existing occupations missing desc
ARCH_DESC = {
    'working': lambda l: f"Worked as {l.lower()} before being pulled into God's Space.",
    'combat': lambda l: f"Trained as {l.lower()}. Experienced in high-stress, dangerous situations.",
    'medical': lambda l: f"Healthcare professional who worked as {l.lower()}. Trained in medical care.",
    'technical': lambda l: f"Technical specialist skilled as {l.lower()}. Adept with complex systems.",
    'academic': lambda l: f"Educated professional who worked as {l.lower()}. Deeply knowledgeable in their field.",
    'creative': lambda l: f"Creative force who worked as {l.lower()}. Expresses through their art.",
    'athletic': lambda l: f"Physically trained as {l.lower()}. Body is their primary instrument.",
    'investigative': lambda l: f"Investigator who worked as {l.lower()}. Trained to find answers.",
    'negative': lambda l: f"A person who was {l.lower()}. Severely disadvantaged in life.",
    'mystery': lambda l: f"Enigmatic figure. Worked as {l.lower()}. What they actually did is unclear."
}
for o in data['occupations']:
    if 'desc' not in o or not o['desc']:
        fn = ARCH_DESC.get(o.get('archetype',''), lambda l: f"Worked as {l.lower()}.")
        o['desc'] = fn(o['label'])

data['occupations'].extend(NEW)
print(f"\nNEW occupations: {sum(CNT.values())}")
print(f"By rarity: {CNT}")
print(f"Total occupations: {len(data['occupations'])}")

# Now handle hobbies
HOBBIES = []
hobby_seq = [0]

for hf in ['hobbies.json', 'hobbies2.json', 'hobbies3.json']:
    hpath = Path(r'C:\Users\CC-Student\AppData\Local\Temp\opencode') / hf
    if hpath.exists():
        with open(hpath, 'r', encoding='utf-8') as f:
            hdata = json.load(f)
        for entry in hdata:
            hobby_seq[0] += 1
            label, rarity, skills, alignment = entry
            HOBBIES.append(dict(
                id=f"hobby-{hobby_seq[0]:05d}",
                label=label,
                rarity=rarity,
                skills=skills,
                alignment=alignment
            ))
        print(f"Loaded {len(hdata)} hobbies from {hf}")
    else:
        print(f"NOT FOUND: {hf}")

data['hobbies'] = HOBBIES
print(f"Total hobbies: {len(HOBBIES)}")

# Save
with open(TEAM_GEN, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Saved team-gen.json - DONE!")
