import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('system/team-gen.json', encoding='utf-8') as f:
    d = json.load(f)

occs = d['occupations']

# 1. Stat ceiling violations (any range exceeding 19)
over19 = []
for o in occs:
    for stat in ['str','agi','end','int','lck','psy']:
        r = o.get(stat, [0, 0])
        if isinstance(r, list) and len(r) == 2 and r[1] > 19:
            over19.append((o['label'], stat, r))
print(f'Occupations with stat range > 19: {len(over19)}')
for label, stat, r in over19[:20]:
    print(f'  {label}: {stat}={r}')

# 2. Rarity field presence
with_rarity    = sum(1 for o in occs if 'rarity' in o)
without_rarity = sum(1 for o in occs if 'rarity' not in o)
print(f'\nOccupations WITH rarity: {with_rarity} | WITHOUT: {without_rarity}')

# 3. Nationality weight field
nats = d['nationalities']
with_weight = sum(1 for n in nats if 'weight' in n)
print(f'\nNationalities with weight field: {with_weight}/{len(nats)}')

# 4. Counts
print(f'\nHobbies: {len(d.get("hobbies", []))}')
print(f'Guide occupations: {len(d.get("guide_occupations", []))}')
print(f'Nationalities: {[n["country"] for n in nats]}')

# 5. Occupation tags check
with_tags    = sum(1 for o in occs if 'tags' in o)
without_tags = sum(1 for o in occs if 'tags' not in o)
print(f'\nOccupations with tags: {with_tags} | without: {without_tags}')
if with_tags:
    sample = next(o for o in occs if 'tags' in o)
    print(f'  Sample tags: {sample["label"]} -> {sample["tags"]}')

# 6. Check character-traits.json skill stat field
with open('system/character-traits.json', encoding='utf-8') as f:
    ct = json.load(f)
pool = ct.get('pool', [])
skills = [t for t in pool if t['type'] == 'skill']
weaks  = [t for t in pool if t['type'] == 'weakness']
has_stat_field = sum(1 for s in skills if 'stat' in s)
has_max_field  = sum(1 for s in skills if 'max' in s)
has_min_field  = sum(1 for s in skills if 'min' in s)
print(f'\nSkill pool: {len(skills)} | has stat: {has_stat_field} | has max: {has_max_field} | has min: {has_min_field}')
print(f'Weakness pool: {len(weaks)}')
# Show stat range overview
maxes = [s['max'] for s in skills if 'max' in s]
if maxes:
    print(f'Skill max values: min={min(maxes)} max={max(maxes)} avg={sum(maxes)/len(maxes):.1f}')
# Sample skills across rarities
for rarity in ['common','uncommon','rare','very_rare','legendary']:
    sample = next((s for s in skills if s.get('rarity') == rarity), None)
    if sample:
        print(f'  [{rarity}] {sample["name"]} stat={sample.get("stat")} max={sample.get("max")}')
