#!/usr/bin/env python3
"""
Character Generator for Terror Infinity RPG.
Reads team-gen.json, character-traits.json, personality-traits.json
to generate complete NPC character sheets in game.json NPC format.

Usage:
  python tools/character_generator.py              # print one random character
  python tools/character_generator.py --count 5    # print 5 characters
  python tools/character_generator.py --json       # print as JSON (use with > npc.json)
  python tools/character_generator.py --guide       # generate a guide instead of NPC
  python tools/character_generator.py --nationality German  # force a nationality
  python tools/character_generator.py --gender M    # force gender (M/F)
"""

import json, random, sys, argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TEAM_GEN = ROOT / 'system' / 'team-gen.json'
CHAR_TRAITS = ROOT / 'system' / 'character-traits.json'
PERSONALITY = ROOT / 'system' / 'personality-traits.json'

RARITY_WEIGHTS = {
    'common': 40, 'uncommon': 30, 'rare': 16, 'very_rare': 10, 'legendary': 4,
}

SKILL_LEVELS = ['beginner', 'novice', 'skilled', 'trained', 'expert', 'master', 'legendary']

# Numeric proficiency ranges per text level (capped at skill's own max field)
LEVEL_RANGES = {
    'beginner':  (2,  7),
    'novice':    (4,  10),
    'skilled':   (7,  13),
    'trained':   (10, 14),
    'expert':    (13, 17),
    'master':    (16, 19),
    'legendary': (18, 22),
}

# Weighted skill draw count per character (mostly 3-5 pool skills)
POOL_SKILL_COUNT_WEIGHTS = [
    (0, 15), (1, 20), (2, 25), (3, 20), (4, 10),
    (5,  5), (6,  3), (7,  1), (8,  1),
]

ALIGNMENT_STANCES = {
    'LG': 'loyal', 'NG': 'loyal', 'CG': 'independent',
    'LN': 'loyal', 'N': 'independent', 'CN': 'independent',
    'LE': 'self-serving', 'NE': 'self-serving', 'CE': 'self-serving',
}

with open(TEAM_GEN, 'r', encoding='utf-8') as f:
    DATA = json.load(f)
with open(CHAR_TRAITS, 'r', encoding='utf-8') as f:
    TRAITS_DATA = json.load(f)
with open(PERSONALITY, 'r', encoding='utf-8') as f:
    PERSONALITY_DATA = json.load(f)

NATIONALITIES = DATA['nationalities']
OCCUPATIONS = DATA['occupations']
HOBBIES = DATA['hobbies']
ALIGNMENTS = DATA['alignments']
AGE_RANGE = DATA['age_range']
GENDERS = DATA['genders']
BUILDS = DATA['builds']
SEXUAL_ORIENTATIONS = DATA['sexual_orientations']
GUIDE_OCCUPATIONS = DATA['guide_occupations']
GUIDE_AGES = DATA['guide_ages']
GUIDE_SURVIVED = DATA['guide_survived_movies']

SKILL_POOL = [t for t in TRAITS_DATA['pool'] if t['type'] == 'skill']
WEAKNESS_POOL = [t for t in TRAITS_DATA['pool'] if t['type'] == 'weakness']
PERSONALITY_TRAITS = PERSONALITY_DATA['traits']

PERSONALITY_POS = [t for t in PERSONALITY_TRAITS if t['type'] == 'pos']
PERSONALITY_NEG = [t for t in PERSONALITY_TRAITS if t['type'] == 'neg']


def weighted_choice(items, weight_key='weight'):
    total = sum(item.get(weight_key, 1) for item in items)
    r = random.uniform(0, total)
    running = 0
    for item in items:
        running += item.get(weight_key, 1)
        if r <= running:
            return item
    return items[-1]


def weighted_sample(items, n, weight_key='weight'):
    if n >= len(items):
        return list(items)
    result = []
    pool = list(items)
    for _ in range(n):
        if not pool:
            break
        item = weighted_choice(pool, weight_key)
        result.append(item)
        pool.remove(item)
    return result


def rarity_choice(pool, rarity_key='rarity', boost_overrides=None):
    if not pool:
        return None
    weights = []
    for item in pool:
        r = item.get(rarity_key, 'common')
        w = RARITY_WEIGHTS.get(r, 10)
        if boost_overrides:
            for label_contains, mult in boost_overrides:
                if label_contains.lower() in item.get('label', '').lower():
                    w *= mult
                    break
        weights.append(w)
    total = sum(weights)
    r = random.uniform(0, total)
    running = 0
    for i, w in enumerate(weights):
        running += w
        if r <= running:
            return pool[i]
    return pool[-1]


def rand_in_range(r):
    if isinstance(r, list) and len(r) == 2:
        return random.randint(min(r), max(r))
    return r if isinstance(r, int) else 10


def occupation_skill_level(skill, occ_skills):
    """occ_skills is always a flat list at this point (normalised by _flatten_occ_skills)."""
    if not occ_skills or skill not in occ_skills:
        return None
    idx = occ_skills.index(skill)
    if idx < 2:
        return 'expert'
    elif idx < 5:
        return 'trained'
    else:
        return 'skilled'


def hobby_skill_level(_skill):
    return 'novice'


def build_occupation_boosts(nationality):
    boosts = nationality.get('occupation_boosts', [])
    return [(b['occupation'], b['multiplier']) for b in boosts]


def pick_name(nationality, gender):
    pool_m = nationality.get('male', ['John'])
    pool_f = nationality.get('female', ['Jane'])
    surnames = nationality.get('surnames', ['Doe'])
    if gender == 'M':
        first = random.choice(pool_m)
    else:
        first = random.choice(pool_f)
    last = random.choice(surnames)
    return f"{first} {last}"


def pick_alignment(occupation_tags, hobby_alignments):
    weights = []
    for al in ALIGNMENTS:
        w = al['weight']
        tags = [t.lower() for t in (occupation_tags or [])]
        if 'criminal' in tags and al['code'] in ('LE', 'NE', 'CE', 'CN'):
            w *= 2
        if 'military' in tags or 'law_enforcement' in tags:
            if al['code'] in ('LG', 'LN', 'NG', 'LE'):
                w *= 2
        if 'religious' in tags and al['code'] in ('LG', 'NG', 'LN'):
            w *= 2
        if 'medical' in tags and al['code'] in ('NG', 'LG', 'CG'):
            w *= 2
        if 'power' in tags and al['code'] in ('LE', 'NE', 'CE'):
            w *= 2
        if hobby_alignments:
            if 'good' in hobby_alignments and 'good' not in al['label'].lower():
                w = max(1, w // 2)
            if 'evil' in hobby_alignments and 'evil' not in al['label'].lower():
                w = max(1, w // 2)
        weights.append(w)
    total = sum(weights)
    r = random.uniform(0, total)
    running = 0
    for i, w in enumerate(weights):
        running += w
        if r <= running:
            return ALIGNMENTS[i]
    return ALIGNMENTS[-1]


def pick_physical(nat):
    hair = weighted_choice(nat.get('hair_colors', [{'c': 'Brown', 'w': 100}]))
    eyes = weighted_choice(nat.get('eye_colors', [{'c': 'Brown', 'w': 100}]))
    skin = weighted_choice(nat.get('skin_tones', [{'t': 'Fair', 'w': 100}]))
    build = weighted_choice(BUILDS)
    return hair['c'], eyes['c'], skin['t'], build['label']


def pick_height(nat, gender):
    if gender == 'M':
        r = nat.get('height_male', [165, 185])
    else:
        r = nat.get('height_female', [155, 175])
    return random.randint(r[0], r[1])


def pick_city(nat):
    cities = nat.get('cities', ['Unknown'])
    return random.choice(cities)


def calc_hp(strength, endurance):
    return 30 + endurance * 5


def calc_stamina(strength, endurance):
    return 40 + (strength + endurance) * 3


def calc_mp(psyche_force):
    return psyche_force * 5


def generate_backstory(occupation, nationality, age, city, alignment_code):
    country = nationality['country']
    label = occupation['label']
    al_map = {
        'LG': 'principled', 'NG': 'kind-hearted', 'CG': 'free-spirited',
        'LN': 'disciplined', 'N': 'pragmatic', 'CN': 'unpredictable',
        'LE': 'calculating', 'NE': 'ruthless', 'CE': 'savage',
    }
    trait = al_map.get(alignment_code, 'ordinary')
    templates = [
        f"A {trait} {label.lower()} from {city}, {country}. Pulled from death into God's Space.",
        f"Former {label.lower()} from {city}, {country}. Known as a {trait} sort. Died before they were ready.",
        f"Worked as a {label.lower()} in {city}, {country}. A {trait} person whose life ended too soon.",
    ]
    return random.choice(templates)


def build_personality():
    pos = random.sample(PERSONALITY_POS, min(3, len(PERSONALITY_POS)))
    neg = random.sample(PERSONALITY_NEG, min(2, len(PERSONALITY_NEG)))
    all_traits = pos + neg
    humor_opts = ['Dry', 'Warm', 'Jovial', 'Dark', 'Sarcastic', 'Quiet', 'Biting', 'Self-deprecating']
    composure_opts = ['Steady', 'Tense', 'Calm', 'Anxious', 'Stoic', 'Volatile', 'Collected', 'Nervous']
    disposition_opts = ['Warm', 'Guarded', 'Cold', 'Friendly', 'Abrasive', 'Reserved', 'Open', 'Suspicious']
    return {
        'humor': random.choice(humor_opts),
        'composure': random.choice(composure_opts),
        'disposition': random.choice(disposition_opts),
    }, [t['name'] for t in all_traits]


def generate_quirk(occupation_tags, personality_names):
    quirks = [
        "Talks to themselves when under pressure.",
        "Hums old songs when nervous.",
        "Counts steps obsessively.",
        "Refuses to go first through any doorway.",
        "Hoards small objects 'just in case.'",
        "Never sits with their back to a room.",
        "Checks corners constantly.",
        "Makes dark jokes about their own death.",
        "Whistles when scared.",
        "Touches walls as they walk past them.",
        "Always carries something in their right hand.",
        "Checks their pulse every few minutes.",
        "Cannot sleep without light.",
        "Clenches fists when lying.",
    ]
    if 'military' in [t.lower() for t in (occupation_tags or [])]:
        quirks.insert(0, "Still follows military protocol for entering rooms.")
    if 'medical' in [t.lower() for t in (occupation_tags or [])]:
        quirks.insert(0, "Sterilizes everything within reach obsessively.")
    if 'criminal' in [t.lower() for t in (occupation_tags or [])]:
        quirks.insert(0, "Never reveals their real name. Has three 'fake' names ready.")
    return random.choice(quirks)


def generate_fear(occupation_tags):
    fears = [
        "Being trapped in small spaces.", "Heights.", "Drowning.",
        "Fire.", "Being abandoned.", "Losing their mind.",
        "The dark.", "Being helpless.", "Spiders.",
        "Being buried alive.", "Needles.", "Crowds.",
        "Silence.", "Loud noises.", "Being watched.",
    ]
    if 'military' in [t.lower() for t in (occupation_tags or [])]:
        fears.insert(0, "IEDs and ambushes.")
    if 'medical' in [t.lower() for t in (occupation_tags or [])]:
        fears.insert(0, "Being the patient instead of the doctor.")
    return random.choice(fears)


def generate_goals(alignment_label):
    goals_pool = {
        'good': [
            "Protect the weaker members of the team.",
            "Find a way home.",
            "Save as many people as possible.",
            "Make sure nobody dies because of their inaction.",
        ],
        'neutral': [
            "Survive. Everything else is secondary.",
            "Get strong enough to never feel helpless.",
            "Figure out what this place really is.",
            "Find an edge and get stronger.",
        ],
        'evil': [
            "Become the strongest, no matter the cost.",
            "Acquire power. Use others as tools.",
            "Never be vulnerable again.",
            "Dominate or die.",
        ],
    }
    label_lc = alignment_label.lower()
    if 'good' in label_lc:
        pool = goals_pool['good']
    elif 'evil' in label_lc:
        pool = goals_pool['evil']
    else:
        pool = goals_pool['neutral']
    return random.sample(pool, min(3, len(pool)))


def level_to_value(level: str, skill_max: int = 19) -> int:
    """Roll a numeric proficiency value (1-skill_max) for a text level."""
    lo, hi = LEVEL_RANGES.get(level, (4, 12))
    return random.randint(lo, min(hi, skill_max))


def _flatten_occ_skills(raw) -> list:
    """Normalise occupation skills to a flat list regardless of format."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        # e.g. {'basic': ['firstaid', ...], 'advanced': ['surgery', ...]}
        flat = []
        for tier, items in raw.items():
            if isinstance(items, list):
                flat.extend(items)
        return flat
    return []


def generate_skills(occupation, hobbies):
    """
    Build skills dict combining:
      1. Occupation skills (guaranteed, high level)
      2. Hobby skills (practiced, novice)
      3. Random draws from the 1000-skill pool (weighted by rarity)
    Each entry: {level, value, source}
    """
    skills_out = {}

    # 1. Occupation skills
    occ_skills = _flatten_occ_skills(occupation.get('skills', []))
    for s in occ_skills:
        level = occupation_skill_level(s, occ_skills) or 'skilled'
        skills_out[s] = {'level': level, 'value': level_to_value(level), 'source': 'occupation'}

    # 2. Hobby skills
    seen_hobby = set()
    for h in hobbies:
        for s in h.get('skills', []):
            if s in seen_hobby or s in skills_out:
                continue
            seen_hobby.add(s)
            level = 'novice'
            skills_out[s] = {'level': level, 'value': level_to_value(level), 'source': 'hobby'}

    MAX_SKILLS = 20

    # 3. Pool skills (the 1000-skill character-traits pool)
    counts, weights = zip(*POOL_SKILL_COUNT_WEIGHTS)
    n_pool = random.choices(counts, weights=weights)[0]
    # Don't exceed cap
    n_pool = min(n_pool, MAX_SKILLS - len(skills_out))
    if n_pool > 0:
        existing_names = {k.lower() for k in skills_out}
        pool_copy = [s for s in SKILL_POOL if s['name'].lower() not in existing_names]
        drawn = weighted_sample(pool_copy, n_pool, weight_key='weight') if pool_copy else []
        for sk in drawn:
            # Rarity → default level mapping
            rarity_level = {
                'common': 'novice', 'uncommon': 'skilled',
                'rare': 'trained', 'very_rare': 'expert', 'legendary': 'master',
            }.get(sk.get('rarity', 'common'), 'novice')
            sk_max = sk.get('max', 19)
            skills_out[sk['name']] = {
                'level': rarity_level,
                'value': level_to_value(rarity_level, sk_max),
                'source': 'background',
                'stat': sk.get('stat'),
            }

    # Hard cap: if hobbies already pushed over the limit, trim background pool entries
    if len(skills_out) > MAX_SKILLS:
        # Keep occupation skills first, then trim from hobby/background
        occ_keys = [k for k, v in skills_out.items() if v.get('source') == 'occupation']
        other_keys = [k for k, v in skills_out.items() if v.get('source') != 'occupation']
        keep = set(occ_keys) | set(other_keys[:MAX_SKILLS - len(occ_keys)])
        skills_out = {k: v for k, v in skills_out.items() if k in keep}

    return skills_out


def generate_weaknesses(skill_count: int) -> list:
    """
    Draw weaknesses scaled to skill count (~2 per 10 skills).
    skill_count=5 → ~1, =10 → ~2, =15 → ~3, =20 → ~4
    """
    base = max(1, round(skill_count / 5))
    variance = random.choices([-1, 0, 1], weights=[15, 60, 25])[0]
    n = max(1, min(6, base + variance))
    result, chosen, attempts = [], set(), 0
    while len(result) < n and attempts < 30:
        w = rarity_choice(WEAKNESS_POOL)
        if w and w['id'] not in chosen:
            chosen.add(w['id'])
            result.append(w)
        attempts += 1
    return result


def generate_npc(gender_override=None, nationality_override=None, is_guide=False):
    gender_data = weighted_choice(GENDERS)
    gender_label = gender_data['label']
    if gender_override == 'M':
        gender_label = 'Male'
    elif gender_override == 'F':
        gender_label = 'Female'

    if nationality_override:
        nat = next((n for n in NATIONALITIES if n['country'].lower() == nationality_override.lower()), None)
        if not nat:
            print(f"Warning: nationality '{nationality_override}' not found, picking random.", file=sys.stderr)
            nat = weighted_choice(NATIONALITIES)
    else:
        nat = weighted_choice(NATIONALITIES)

    gender_code = 'M' if gender_label == 'Male' else 'F'
    name = pick_name(nat, gender_code)

    boosts = build_occupation_boosts(nat)

    if is_guide:
        occupation = random.choice(GUIDE_OCCUPATIONS)
        age = random.randint(GUIDE_AGES['min'], GUIDE_AGES['max'])
        movies_survived = random.randint(GUIDE_SURVIVED['min'], GUIDE_SURVIVED['max'])
        rank = 'F' if movies_survived >= 5 else 'Unranked'
        occ_label = occupation['label']
        occ_id = occupation['id']
        occ_tags = occupation.get('tags', [])
        level = max(1, movies_survived)
        xp = 0
        genetic_locks = 1 if rank != 'Unranked' else 0
    else:
        occupation = rarity_choice(OCCUPATIONS, boost_overrides=boosts)
        age = random.randint(AGE_RANGE['min'], AGE_RANGE['max'])
        movies_survived = 0
        rank = 'Unranked'
        occ_label = occupation['label']
        occ_id = occupation['id']
        occ_tags = occupation.get('tags', [])
        level = 1
        xp = 0
        genetic_locks = 0

    str_val = rand_in_range(occupation['str'])
    agi_val = rand_in_range(occupation['agi'])
    end_val = rand_in_range(occupation['end'])
    int_val = rand_in_range(occupation['int'])
    lck_val = rand_in_range(occupation['lck'])
    psy_val = rand_in_range(occupation.get('psy', [0, 5]))

    # Clamp human stats: most occupations cap at 19; elite/enhanced can exceed
    human_cap = 19
    elite_tags = {'enhanced', 'superhuman', 'experimental', 'divine', 'monster'}
    is_elite = bool(elite_tags.intersection(set(t.lower() for t in occ_tags)))
    if not is_elite:
        str_val = min(str_val, human_cap)
        agi_val = min(agi_val, human_cap)
        end_val = min(end_val, human_cap)
        int_val = min(int_val, human_cap)
        lck_val = min(lck_val, human_cap)
        psy_val = min(psy_val, human_cap)

    hp      = 30 + end_val * 5
    stamina = 40 + (str_val + end_val) * 3
    mp      = psy_val * 5

    num_hobbies = random.choices([1, 2, 3, 4, 5], weights=[5, 25, 35, 25, 10])[0]
    hobbies = []
    chosen_h_ids = set()
    for _ in range(num_hobbies):
        h = rarity_choice(HOBBIES)
        if h and h['id'] not in chosen_h_ids:
            chosen_h_ids.add(h['id'])
            hobbies.append(h)
    hobby_alignments = list(set(h.get('alignment', 'neutral') for h in hobbies))

    alignment = pick_alignment(occ_tags, hobby_alignments)
    team_stance = ALIGNMENT_STANCES.get(alignment['code'], 'independent')

    hobbies_skills = []
    for h in hobbies:
        for s in h.get('skills', []):
            hobbies_skills.append(s)

    personality, personality_names = build_personality()
    quirks = generate_quirk(occ_tags, personality_names)
    fears = generate_fear(occ_tags)
    goals = generate_goals(alignment['label'])

    hair, eyes, skin, build = pick_physical(nat)
    height = pick_height(nat, gender_code)
    city = pick_city(nat)
    sexual_orientation = weighted_choice(SEXUAL_ORIENTATIONS)['label']
    backstory = generate_backstory(occupation, nat, age, city, alignment['code'])

    skills = generate_skills(occupation, hobbies)
    weaknesses = generate_weaknesses(len(skills))

    npc_id = f"npc-{random.randint(1000, 9999)}"

    result = {
        'id': npc_id,
        'name': name,
        'nationality': nat['country'],
        'age': age,
        'gender': gender_label,
        'height_cm': height,
        'build': build,
        'hair_color': hair,
        'eye_color': eyes,
        'skin_tone': skin,
        'city': city,
        'sexual_orientation': sexual_orientation,
        'occupation': occ_label,
        'occupation_id': occ_id,
        'occupation_tags': occ_tags,
        'backstory': backstory,
        'alive': True,
        'hp': hp,
        'hp_max': hp,
        'mp': mp,
        'mp_max': mp,
        'stamina': stamina,
        'stamina_max': stamina,
        'status': 'Active',
        'strength': str_val,
        'agility': agi_val,
        'endurance': end_val,
        'intelligence': int_val,
        'luck': lck_val,
        'psyche_force': psy_val,
        'rank': rank,
        'level': level,
        'xp': xp,
        'skills': skills,
        'personality': personality,
        'personality_traits': personality_names,
        'background': f"{occ_label}, {city} ({nat['country']})",
        'quirk': quirks,
        'fear': fears,
        'goals': goals,
        'alignment': alignment['label'],
        'team_stance': team_stance,
        'loyalty': random.randint(40, 80),
        'location': 'unknown',
        'sublocation': None,
    }

    if is_guide:
        result['movies_survived'] = movies_survived
        result['knowledge'] = []
        result['death_movie'] = None
        result['death_description'] = None
        result['introduced'] = False
        result['genetic_locks_opened'] = genetic_locks
        result['enhancements'] = []

    result['hobbies'] = [{'id': h['id'], 'label': h['label'], 'alignment': h.get('alignment', 'neutral')} for h in hobbies]
    result['weaknesses'] = []
    for w in weaknesses:
        entry = {'id': w['id'], 'name': w['name']}
        if w.get('heals_on_movie_end'):
            entry['heals_on_movie_end'] = True
        result['weaknesses'].append(entry)

    return result


def format_output(char, as_json=False):
    if as_json:
        return json.dumps(char, indent=2, ensure_ascii=False)
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  {char['name']} - {char['nationality']}, {char['age']}")
    lines.append(f"  {char['occupation']} | {char['alignment']}")
    lines.append(f"{'='*60}")
    lines.append(f"  STR {char['strength']:>2}  AGI {char['agility']:>2}  END {char['endurance']:>2}")
    lines.append(f"  INT {char['intelligence']:>2}  LCK {char['luck']:>2}  PSY {char['psyche_force']:>2}")
    lines.append(f"  HP {char['hp']}/{char['hp_max']}  MP {char['mp']}/{char['mp_max']}  STA {char['stamina']}/{char['stamina_max']}")
    lines.append(f"  Rank: {char['rank']}  Build: {char['build']}  Height: {char['height_cm']}cm")
    lines.append(f"  Hair: {char['hair_color']}  Eyes: {char['eye_color']}  Skin: {char['skin_tone']}")
    lines.append(f"")
    lines.append(f"  Backstory: {char['backstory']}")
    lines.append(f"")
    if char.get('movies_survived', 0) > 0:
        lines.append(f"  Movies survived: {char['movies_survived']}")
    lines.append(f"  Personality: {', '.join(char['personality_traits'])}")
    lines.append(f"  Humor: {char['personality']['humor']}  Composure: {char['personality']['composure']}  Disposition: {char['personality']['disposition']}")
    lines.append(f"  Quirk: {char['quirk']}")
    lines.append(f"  Fear: {char['fear']}")
    if char['goals']:
        lines.append(f"  Goals: {'; '.join(char['goals'])}")
    lines.append(f"")
    if char.get('hobbies'):
        lines.append(f"  Hobbies ({len(char['hobbies'])}): {', '.join(h['label'] for h in char['hobbies'])}")
    lines.append(f"  Skills ({len(char['skills'])}):")
    for s, v in sorted(char['skills'].items()):
        lines.append(f"    {s:>25} -> {v['level']}")
    if char.get('weaknesses'):
        lines.append(f"  Weaknesses ({len(char['weaknesses'])}):")
        for w in char['weaknesses']:
            lines.append(f"    - {w['name']}")
    lines.append(f"{'='*60}")
    return '\n'.join(lines)


def main():
    # Fix Windows codepage crash when names contain non-ASCII chars
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description='Generate Terror Infinity RPG characters')
    parser.add_argument('--count', type=int, default=1, help='Number of characters to generate')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--guide', action='store_true', help='Generate a guide character')
    parser.add_argument('--nationality', type=str, default=None, help='Force a nationality')
    parser.add_argument('--gender', type=str, default=None, choices=['M', 'F'], help='Force gender')
    args = parser.parse_args()

    chars = []
    for i in range(args.count):
        char = generate_npc(
            gender_override=args.gender,
            nationality_override=args.nationality,
            is_guide=args.guide,
        )
        chars.append(char)

    if args.count == 1:
        output = format_output(chars[0], as_json=args.json)
    else:
        if args.json:
            output = json.dumps(chars, indent=2, ensure_ascii=False)
        else:
            output = '\n'.join(format_output(c) for c in chars)

    print(output)


if __name__ == '__main__':
    main()
