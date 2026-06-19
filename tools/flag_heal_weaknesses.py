#!/usr/bin/env python3
"""Add heals_on_movie_end flags to physical disability weaknesses."""
import json
from pathlib import Path

PATH = Path(r'C:\laragon\www\terror-infinity-rpg\system\character-traits.json')
with open(PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Physical disability weakness IDs that heal after a movie
heal_ids = [
    'wk-0413', 'wk-0415', 'wk-0327',  # paralysis
    'wk-0320', 'wk-0321',             # total blind/deaf
    'wk-0328', 'wk-0329', 'wk-0330', 'wk-0331',  # missing limbs
    'wk-0332', 'wk-0333', 'wk-0334', 'wk-0335', 'wk-0336',  # amputations
    'wk-0200', 'wk-0201',             # one eye/ear
    'wk-0203',                         # stutter
    'wk-0208', 'wk-0209',             # missing fingers/toes
    'wk-0128', 'wk-0130',             # color/night blindness
]

count = 0
for t in data['pool']:
    if t['id'] in heal_ids:
        t['heals_on_movie_end'] = True
        count += 1
        # Add GM note for total paralysis
        if t['id'] in ('wk-0413', 'wk-0415'):
            t['gm_note'] = "God's Space provides a survival mechanism — GM discretion on what form it takes (mobility aid, sensory compensation, etc.)"
        if t['id'] == 'wk-0413':
            t['desc'] = 'Complete paralysis. Totally unable to move from the neck down.'
        elif t['id'] == 'wk-0415':
            t['desc'] = 'Full body paralysis. No voluntary movement at all, including facial muscles and eyes.'
        elif t['id'] == 'wk-0327':
            t['desc'] = 'Partial paralysis affecting some limbs but not all.'

print(f'Added heals_on_movie_end to {count} weaknesses')

with open(PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('Saved.')
