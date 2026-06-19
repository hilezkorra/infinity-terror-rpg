#!/usr/bin/env python3
"""
Terror Infinity RPG — AI Portrait Generator (Local A1111)
==========================================================
Generates VN-quality character portraits using a locally running
AUTOMATIC1111 Stable Diffusion WebUI.

  portrait mode  (default) — single posed card-cover portrait per character
  sheet mode     (--sheet) — 3-view front/side/back character-sheet turnaround

════════════════════════════════════════════════════════════════
 ONE-TIME SETUP
════════════════════════════════════════════════════════════════

 1. Install A1111:
      git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
      Run install-windows.bat (or webui-user.bat on first launch)

 2. Download Dark Sushi Mix 2.5D — Brighter variant (CivitAI #24779)
      → place .safetensors in  <a1111>/models/Stable-diffusion/

 3. Download VAE "vae-ft-mse-840000-ema-pruned.ckpt"
      https://huggingface.co/stabilityai/sd-vae-ft-mse-original
      → place in  <a1111>/models/VAE/
      → set it in A1111 → Settings → VAE → SD VAE

 4. (Optional, for --sheet) Download a character-sheet LoRA from CivitAI
      Search: "character sheet turnaround"
      → place .safetensors in  <a1111>/models/Lora/
      → set  SHEET_LORA_NAME  below to match the filename (no extension)

 5. Edit webui-user.bat and add the API flag + VRAM option:
      set COMMANDLINE_ARGS=--api --medvram
      (use --lowvram if you still get out-of-memory errors)

 6. Launch A1111 and wait for "Running on local URL: http://127.0.0.1:7860"

════════════════════════════════════════════════════════════════
 USAGE
════════════════════════════════════════════════════════════════

  python generate-portraits.py              # posed portrait (card cover) for all
  python generate-portraits.py --sheet      # 3-view turnaround sheets only
  python generate-portraits.py --all        # both portrait + sheet
  python generate-portraits.py --force      # overwrite existing generated files
  python generate-portraits.py chen-wei     # one specific character only

If A1111 is not running, portraits fall back to DiceBear avatars automatically.
Sheets are skipped (require A1111).
"""

import json, re, os, sys, time, hashlib, base64
import urllib.request, urllib.parse

# ── Paths ─────────────────────────────────────────────────────────────
ROOT      = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
GAME_JSON = os.path.join(ROOT, 'data', 'game.json')
PORTRAITS = os.path.join(ROOT, 'assets', 'portraits')

# ── A1111 Config ──────────────────────────────────────────────────────
A1111_URL         = 'http://localhost:7860'
IMG_W, IMG_H      = 512, 768
STEPS             = 28
CFG               = 7.0
SAMPLER           = 'DPM++ 2M Karras'

# Character-sheet LoRA — set to filename without extension, or '' to disable
SHEET_LORA_NAME   = 'CharacterSheet'
SHEET_LORA_WEIGHT = 0.75

# Files at or above this size are hand-drawn — never overwrite
HAND_DRAWN_MIN_KB = 50

# ── Prompts — shared prefixes ─────────────────────────────────────────
_QA = '(masterpiece, best quality:1.2), highly detailed, anime illustration, 2.5D, clean lineart, soft dramatic lighting, '
_QH = '(masterpiece, best quality:1.2), highly detailed, horror illustration, dramatic chiaroscuro lighting, deep shadows, '

NEG_ALLY = (
    'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, '
    'cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, '
    'username, blurry, bad proportions, deformed, ugly, extra limbs, fused fingers, '
    'too many fingers, long neck, mutation, mutated, poorly drawn face, poorly drawn hands'
)
NEG_ENEMY = NEG_ALLY + (
    ', human face, normal human, realistic proportions, happy expression, cute, '
    'clean skin, bright colors, cheerful'
)

# ── Character data ────────────────────────────────────────────────────
# portrait = personality-based posed card-cover portrait (512x768)
# sheet    = 3-view front/side/back turnaround reference sheet
# enemy    = True → uses horror prompts + NEG_ENEMY

CHARS = {

    # ── Hand-drawn portraits (always skipped) ─────────────────────────
    'igor-pundzin': None,
    'yuki-tanaka':  None,

    # ═════════════════════════════════════════════════════════════════
    #  ALLIES
    # ═════════════════════════════════════════════════════════════════

    'chen-wei': {
        'enemy': False,
        'portrait': (
            _QA +
            '1boy, young Chinese man, short neat black hair, sharp dark determined eyes, '
            'modern dark tactical jacket, white undershirt, slight collar, '
            'arms firmly crossed over chest, leaning slightly forward, weight on front foot, '
            'unflinching direct gaze into camera, jaw set, quiet stubborn resolve, '
            'upper body portrait, plain very dark background, subtle rim lighting'
        ),
        'sheet': (
            _QA +
            '1boy, young Chinese man, short black hair, dark tactical jacket, white undershirt, '
            'character reference sheet, front view, side view, back view, multiple views, '
            'turnaround, full body, simple light grey background, clean reference art'
        ),
    },

    'dmitri-sokolov': {
        'enemy': False,
        'portrait': (
            _QA +
            '1boy, broad muscular Russian man, short brown hair, stern weathered face, '
            'deep-set eyes, prominent jaw, facial scar on cheek, '
            'dark military combat jacket, tactical vest with pouches, '
            'parade rest stance, hands clasped firmly behind back, feet planted wide, '
            'chin elevated, looking slightly downward, iron discipline expression, '
            'upper body portrait, plain very dark background, strong side lighting'
        ),
        'sheet': (
            _QA +
            '1boy, broad Russian man, short brown hair, facial scar, dark military jacket, tactical vest, '
            'character reference sheet, front view, side view, back view, multiple views, '
            'turnaround, full body, simple light grey background'
        ),
    },

    'sophia-harlow': {
        'enemy': False,
        'portrait': (
            _QA +
            '1girl, young American woman, shoulder-length auburn hair with soft waves, '
            'sharp bright hazel eyes, subtle natural makeup, small earrings, '
            'dark fitted practical jacket over light top, '
            'one hand on hip, other hand raised with two fingers lightly touching chin, '
            'head tilted slightly to one side, knowing confident smile, relaxed intelligence, '
            'upper body portrait, plain very dark background'
        ),
        'sheet': (
            _QA +
            '1girl, young American woman, auburn hair, dark fitted jacket, '
            'character reference sheet, front view, side view, back view, multiple views, '
            'turnaround, full body, simple light grey background'
        ),
    },

    'aleksei-petrov': {
        'enemy': False,
        'portrait': (
            _QA +
            '1boy, distinguished Russian man in his 50s, silver-streaked dark hair swept back, '
            'weathered lined face, calm heavy-lidded powerful eyes, broad shoulders, '
            'long dark military greatcoat with subtle insignia, '
            'standing perfectly upright, arms loosely at sides, weight balanced, '
            'serene immovable expression, patience of a man who has seen everything, '
            'upper body portrait, plain very dark background, cool blue rim light'
        ),
        'sheet': (
            _QA +
            '1boy, older Russian man, silver-streaked hair, long dark military greatcoat, '
            'character reference sheet, front view, side view, back view, multiple views, '
            'turnaround, full body, simple light grey background'
        ),
    },

    'vera-kessler': {
        'enemy': False,
        'portrait': (
            _QA +
            '1girl, German woman, platinum blonde hair pulled back tightly, pale ice-blue eyes, '
            'sharp angular features, thin lips, no expression, '
            'dark form-fitting combat uniform, tactical belt, subtle shoulder padding, '
            'body angled 15 degrees, arms hanging at sides with contained tension, '
            'cold unflinching direct stare into camera, calculating and lethal stillness, '
            'upper body portrait, plain very dark background, cool harsh lighting'
        ),
        'sheet': (
            _QA +
            '1girl, German woman, platinum blonde hair, dark combat uniform, tactical belt, '
            'character reference sheet, front view, side view, back view, multiple views, '
            'turnaround, full body, simple light grey background'
        ),
    },

    # ═════════════════════════════════════════════════════════════════
    #  ENEMIES
    # ═════════════════════════════════════════════════════════════════

    'licker': {
        'enemy': True,
        'portrait': (
            _QH +
            'Resident Evil Licker mutant creature, no skin, fully exposed raw glistening red muscle, '
            'oversized brain protruding from skull, long razor-sharp bone claws, '
            'whip-like tongue 3 meters long lashing forward, '
            'low aggressive predator crouch, weight distributed on all four limbs, '
            'body coiled ready to spring, head low and forward, '
            'horror creature portrait, deep red-black background, faint mist'
        ),
        'sheet': (
            _QH +
            'Resident Evil Licker creature, exposed red muscle, exposed brain, bone claws, long tongue, '
            'creature reference sheet, front view, side view, back view, multiple views, '
            'turnaround, full body, dark charcoal background'
        ),
    },

    'zombie': {
        'enemy': True,
        'portrait': (
            _QH +
            'horrifying zombie, advanced decomposition, grey-green rotting skin with open wounds, '
            'pale milky glazed dead eyes, jaw hanging open, '
            'torn blood-soaked clothing, patches of exposed bone, '
            'shambling forward with both arms outstretched reaching upward, '
            'head drooping 30 degrees to the right, lurching undead gait, '
            'horror creature portrait, dark foggy background, sickly green ambient light'
        ),
        'sheet': (
            _QH +
            'horrifying zombie, rotting grey skin, dead eyes, torn bloody clothes, exposed wounds, '
            'creature reference sheet, front view, side view, back view, multiple views, '
            'turnaround, full body, dark charcoal background'
        ),
    },

    'nemesis-fragment': {
        'enemy': True,
        'portrait': (
            _QH +
            'fragment of the Nemesis parasite organism, writhing mass of black wet organic tentacles, '
            'pulsating dark flesh with visible veins, '
            'glowing molten crimson red core visible at the center of the mass, '
            'dripping viscous dark ichor, '
            'tentacles erupting outward and upward explosively in all directions, '
            'rising aggression, no clear head or face, pure alien horror, '
            'creature portrait, pitch black background, deep red glow from within'
        ),
        'sheet': (
            _QH +
            'Nemesis parasite fragment, black tentacles, glowing red core, organic mass, ichor dripping, '
            'creature reference sheet, multiple views and forms, size reference, '
            'dark charcoal background, crimson accent lighting'
        ),
    },

    't-103-tyrant': {
        'enemy': True,
        'portrait': (
            _QH +
            'T-103 Tyrant from Resident Evil, massive towering humanoid mutant nearly 3 meters tall, '
            'pale corpse-grey skin with visible mutations, '
            'exposed pulsating oversized heart on chest, '
            'long tattered black trench coat, torn at edges, '
            'right hand transformed into single enormous curved bone claw, left hand normal but massive, '
            'standing with arms slightly away from body, slightly hunched forward, '
            'radiating oppressive overwhelming physical dominance, '
            'looking down, tiny eyes cold and dead, '
            'horror creature portrait, dark rain-soaked industrial background, cold mist'
        ),
        'sheet': (
            _QH +
            'T-103 Tyrant, massive humanoid mutant, grey skin, exposed heart, black trench coat, '
            'right bone claw, character reference sheet, front view, side view, back view, '
            'multiple views, turnaround, full body, dark charcoal background'
        ),
    },

    'unknown': {
        'enemy': True,
        'portrait': (
            _QH +
            'mysterious SSS-rank horror entity, '
            'barely perceptible dark humanoid silhouette dissolving into void, '
            'two points of glowing crimson light where eyes should be, '
            'living darkness tendrils spreading slowly outward in all directions, '
            'implied presence far larger than visible form suggests, '
            'hovering slightly above ground, no solid edges, '
            'no face, no features, only wrongness and dread, '
            'entity portrait, absolute pitch black void background, '
            'faint deep red ambient pulse, negative space composition'
        ),
        'sheet': (
            _QH +
            'mysterious void entity, glowing red eyes, darkness tendrils, humanoid silhouette, '
            'entity reference sheet, multiple manifestation forms, size scale, '
            'absolute black background, crimson glow'
        ),
    },
}

# ── Slug helper ────────────────────────────────────────────────────────
def slugify(name):
    s = re.sub(r'[^a-z0-9-]', '', re.sub(r'\s+', '-', (name or '').strip().lower()))
    return s or 'unknown'

# ── Collect chars from game.json not in CHARS ─────────────────────────
def collect_extra(g):
    extras = {}
    def add(name, role):
        if not name or name == '???': return
        slug = slugify(name)
        if slug not in CHARS and slug not in extras:
            extras[slug] = {'name': name, 'role': role}
    ch = g.get('character') or {}
    add(ch.get('name'), 'player')
    for c in (g.get('combat') or {}).get('combatants', []):
        add(c.get('name'), c.get('role', 'enemy'))
    team = g.get('team') or []
    for m in (team.get('members', []) if isinstance(team, dict) else team):
        if isinstance(m, dict): add(m.get('name'), m.get('role', 'ally'))
    for _k, v in (g.get('npcs') or {}).items():
        if isinstance(v, dict): add(v.get('name'), v.get('role', 'neutral'))
    guide = g.get('guide') or {}
    if isinstance(guide, dict): add(guide.get('name'), 'ally')
    return extras

def auto_prompts(slug, role):
    """Generate default prompts for characters not in the CHARS dict."""
    is_enemy = role in ('enemy', 'hostile')
    name_hint = slug.replace('-', ' ').title()
    q = _QH if is_enemy else _QA
    portrait = (
        q + (
            f'terrifying horror creature, {name_hint}, aggressive pose, '
            'dark background, dramatic lighting'
            if is_enemy else
            f'character {name_hint}, confident personality pose, '
            'visual novel character portrait, upper body, plain dark background, anime illustration'
        )
    )
    sheet = (
        q + (
            f'horror creature {name_hint}, multiple views, '
            'creature reference sheet, dark charcoal background'
            if is_enemy else
            f'character {name_hint}, character reference sheet, '
            'front view, side view, back view, turnaround, full body, light grey background'
        )
    )
    return {'enemy': is_enemy, 'portrait': portrait, 'sheet': sheet,
            '_name': name_hint, '_role': role}

# ── A1111 API helpers ─────────────────────────────────────────────────
def a1111_ping():
    try:
        req = urllib.request.Request(
            f'{A1111_URL}/sdapi/v1/sd-models',
            headers={'User-Agent': 'TI-PortraitGen'}
        )
        with urllib.request.urlopen(req, timeout=5):
            return True
    except:
        return False

def txt2img(prompt, dest, negative, seed=-1):
    payload = json.dumps({
        'prompt':          prompt,
        'negative_prompt': negative,
        'steps':           STEPS,
        'width':           IMG_W,
        'height':          IMG_H,
        'cfg_scale':       CFG,
        'seed':            seed,
        'sampler_name':    SAMPLER,
        'save_images':     False,
        'send_images':     True,
        'batch_size':      1,
        'n_iter':          1,
    }).encode()
    req = urllib.request.Request(
        f'{A1111_URL}/sdapi/v1/txt2img',
        data=payload,
        headers={'Content-Type': 'application/json', 'User-Agent': 'TI-PortraitGen'}
    )
    with urllib.request.urlopen(req, timeout=360) as r:
        result = json.loads(r.read())
    img_bytes = base64.b64decode(result['images'][0])
    with open(dest, 'wb') as f:
        f.write(img_bytes)
    return len(img_bytes)

# ── DiceBear fallback ─────────────────────────────────────────────────
_BOSS_SLUGS = {'tyrant', 'nemesis', 'cerberus', 'neptune', 'hunter', 'phantom', 'crimson'}
_HEADERS    = {'User-Agent': 'TI-PortraitGen/1.0'}

def dicebear_url(name, slug, role):
    seed = urllib.parse.quote(name.strip())
    if any(b in slug for b in _BOSS_SLUGS):
        style, extra = 'notionists', '&backgroundColor=120808&size=400'
    elif role in ('enemy', 'hostile'):
        style, extra = 'thumbs', '&backgroundColor=1a0a08&shapeColor=8b0000,5c0000,3d0000&size=400'
    else:
        style, extra = 'adventurer', '&backgroundColor=0d1117&radius=6&size=400'
    return f'https://api.dicebear.com/9.x/{style}/png?seed={seed}{extra}'

def download_dicebear(url, dest):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    if len(data) < 500:
        raise ValueError(f'response too small ({len(data)} B)')
    with open(dest, 'wb') as f:
        f.write(data)
    return len(data)

# ── Stable seed ───────────────────────────────────────────────────────
def stable_seed(text):
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 999983

# ── Main ──────────────────────────────────────────────────────────────
def main():
    args        = sys.argv[1:]
    do_portrait = '--sheet' not in args or '--all' in args
    do_sheet    = '--sheet' in args or '--all' in args
    force       = '--force' in args
    # optional: single slug filter  e.g.  python generate-portraits.py chen-wei
    only_slug   = next((a for a in args if not a.startswith('--')), None)

    if not do_portrait and not do_sheet:
        do_portrait = True

    os.makedirs(PORTRAITS, exist_ok=True)

    with open(GAME_JSON, encoding='utf-8-sig') as f:
        g = json.load(f)

    # Merge known CHARS + any new chars from game.json
    all_chars = dict(CHARS)
    for slug, info in collect_extra(g).items():
        all_chars[slug] = auto_prompts(slug, info['role'])

    # Check A1111
    use_a1111 = a1111_ping()
    if use_a1111:
        print(f'[OK] A1111 online at {A1111_URL}')
    else:
        print(f'[--] A1111 not detected at {A1111_URL}')
        print('     Portraits will use DiceBear fallback.')
        print('     To use AI generation: launch A1111 with --api --medvram')
        if do_sheet:
            print('     Sheets require A1111 — skipping sheet mode.')
            do_sheet = False
    print()

    modes = []
    if do_portrait: modes.append(('portrait', ''))
    if do_sheet:    modes.append(('sheet',    '-sheet'))

    col    = max(len(s) for s in all_chars) + 2
    counts = {'gen': 0, 'skip': 0, 'fail': 0}

    for slug in sorted(all_chars):
        if only_slug and slug != only_slug:
            continue

        data = all_chars[slug]

        # ── Hand-drawn slot ──────────────────────────────────────────
        if data is None:
            dest = os.path.join(PORTRAITS, f'{slug}.png')
            if os.path.exists(dest):
                kb = os.path.getsize(dest) // 1024
                print(f'  KEEP   {slug:<{col}} hand-drawn ({kb} KB)')
            else:
                print(f'  SKIP   {slug:<{col}} hand-drawn placeholder (file missing)')
            counts['skip'] += 1
            continue

        is_enemy = data.get('enemy', False)
        negative = NEG_ENEMY if is_enemy else NEG_ALLY

        for mode, suffix in modes:
            dest = os.path.join(PORTRAITS, f'{slug}{suffix}.png')

            # Protect hand-drawn files
            if os.path.exists(dest):
                kb = os.path.getsize(dest) // 1024
                if kb >= HAND_DRAWN_MIN_KB:
                    print(f'  KEEP   {slug:<{col}} [{mode}] hand-drawn ({kb} KB)')
                    counts['skip'] += 1
                    continue
                if not force:
                    print(f'  SKIP   {slug:<{col}} [{mode}] exists ({kb} KB)  [use --force to regen]')
                    counts['skip'] += 1
                    continue

            prompt = data.get(mode, '')
            seed   = stable_seed(slug + mode)

            # Inject sheet LoRA if configured and available
            if mode == 'sheet' and SHEET_LORA_NAME.strip():
                prompt = f'<lora:{SHEET_LORA_NAME}:{SHEET_LORA_WEIGHT}>, ' + prompt

            label  = f'  GEN    {slug:<{col}} [{mode}] '
            print(label, end='', flush=True)

            if use_a1111:
                try:
                    kb = txt2img(prompt, dest, negative=negative, seed=seed) // 1024
                    print(f'OK  ({kb} KB)')
                    counts['gen'] += 1
                    time.sleep(0.5)
                except Exception as e:
                    print(f'FAIL  {e}')
                    counts['fail'] += 1

            elif mode == 'portrait':
                # DiceBear fallback — portrait only, no sheets
                name = data.get('_name', slug.replace('-', ' ').title())
                role = data.get('_role', 'enemy' if is_enemy else 'ally')
                try:
                    url = dicebear_url(name, slug, role)
                    kb  = download_dicebear(url, dest) // 1024
                    print(f'OK  DiceBear ({kb} KB)')
                    counts['gen'] += 1
                    time.sleep(0.4)
                except Exception as e:
                    print(f'FAIL  {e}')
                    counts['fail'] += 1

            else:
                # Sheet mode without A1111 — skip silently
                print('SKIP (needs A1111)')
                counts['skip'] += 1

    line = '-' * 58
    print(f'\n{line}')
    print(f'Generated : {counts["gen"]}')
    print(f'Skipped   : {counts["skip"]}')
    print(f'Failed    : {counts["fail"]}')
    if counts['fail']:
        print('Tip: re-run to retry, or --force to regenerate all.')
    else:
        print('Done. Reload the game to see updated portraits.')

if __name__ == '__main__':
    main()
