import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('system/team-gen.json', encoding='utf-8') as f:
    d = json.load(f)

occs   = d['occupations']
hobbies = d.get('hobbies', [])

print(f'Occupations: {len(occs)}')
print(f'Hobbies:     {len(hobbies)}')

# Occupation rarity distribution
rarity_dist = {}
for o in occs:
    r = o.get('rarity', 'missing')
    rarity_dist[r] = rarity_dist.get(r, 0) + 1
print(f'\nOccupation rarities: {dict(sorted(rarity_dist.items()))}')

# Hobby category/label sampling
hobby_labels = [h['label'] for h in hobbies]
# Group by rough category (first word or known prefix)
print(f'\nHobby sample (first 30): {hobby_labels[:30]}')
print(f'Hobby sample (last 20):  {hobby_labels[-20:]}')

# Check for duplicate IDs
occ_ids    = [o['id'] for o in occs]
hobby_ids  = [h['id'] for h in hobbies]
dup_occ    = len(occ_ids) - len(set(occ_ids))
dup_hobby  = len(hobby_ids) - len(set(hobby_ids))
print(f'\nDuplicate occupation IDs: {dup_occ}')
print(f'Duplicate hobby IDs:      {dup_hobby}')

# Check occupation field completeness
missing_fields = {}
required = ['id','label','archetype','str','agi','end','int','lck','psy','skills','rarity','tags']
for o in occs:
    for f in required:
        if f not in o:
            missing_fields[f] = missing_fields.get(f, 0) + 1
print(f'\nOccupations missing required fields: {missing_fields}')

# Hobby field completeness
hobby_required = ['id','label','rarity','skills']
hobby_missing = {}
for h in hobbies:
    for f in hobby_required:
        if f not in h:
            hobby_missing[f] = hobby_missing.get(f, 0) + 1
print(f'Hobbies missing required fields: {hobby_missing}')
