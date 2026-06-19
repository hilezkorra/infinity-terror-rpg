import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('system/team-gen.json', encoding='utf-8') as f:
    d = json.load(f)

# Find occupations where skills is not a list
bad = [(o['label'], type(o.get('skills')).__name__, o.get('skills'))
       for o in d['occupations'] if not isinstance(o.get('skills'), list)]
print(f'Occupations with non-list skills: {len(bad)}')
for label, t, val in bad[:8]:
    print(f'  {label}: type={t}, value={str(val)[:80]}')

# Check guide occupations too
for o in d['guide_occupations']:
    sk = o.get('skills')
    if not isinstance(sk, list):
        name = o.get('label', '?')
        print(f'Guide occ non-list skills: {name} type={type(sk).__name__}')

# Also check hobbies
bad_h = [(h['label'], type(h.get('skills')).__name__)
         for h in d['hobbies'] if not isinstance(h.get('skills'), list)]
print(f'Hobbies with non-list skills: {len(bad_h)}')
for label, t in bad_h[:5]:
    print(f'  {label}: type={t}')
