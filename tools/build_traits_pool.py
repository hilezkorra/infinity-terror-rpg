#!/usr/bin/env python3
"""
Build the unified skill/weakness pool (1000 skills + 200 weaknesses).
Skills = learned abilities (NOT inherent human traits like walking/talking).
Weaknesses = debilities both mild and severe.

Output: system/character-traits.json
Combined pool with type:"skill" or type:"weakness".
"""

import json, random
from pathlib import Path

random.seed(0)  # deterministic for review

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'system' / 'character-traits.json'

# ── helpers ────────────────────────────────────────────────────
def sid(prefix, n): return f'{prefix}-{n:04d}'
def skill(name, stat, rarity, desc, cap=19):
    return {'id':sid('sk',len(SKILLS)+1),'name':name,'type':'skill','rarity':rarity,
            'stat':stat,'desc':desc,'max':cap}
def weak(name, rarity, desc):
    return {'id':sid('wk',len(WEAKNESSES)+1),'name':name,'type':'weakness','rarity':rarity,'desc':desc}

SKILLS = []
WEAKNESSES = []

# ════════════════════════════════════════════════════════════════
# SKILLS — 1000 total
# ════════════════════════════════════════════════════════════════
# rarity → draw probability (higher = more likely to appear on a character)
#   common:   60‑70% of population (~400 skills)
#   uncommon: 25‑35% (~300 skills)
#   rare:     8‑12% (~160 skills)
#   very_rare: 2‑4% (~100 skills)
#   legendary: <0.5% (~40 skills)

# ── COMMON (≈400) ──────────────────────────────────────────────
C = 'common'
ST = ['endurance','agility','strength','intelligence','charisma','luck','psyche_force']

# Domestic / life skills
for n in [
    'Cooking (basic)','Sweeping','Mopping','Dusting','Laundry','Ironing',
    'Dish washing','Bed making','Food shopping','Budgeting','Sewing (buttons)',
    'Plant watering','Basic home cleaning','Trash disposal','Pet feeding',
    'Wound cleaning','Bandage application','Ice pack use','Thermometer use',
    'Nail clipping','Hair brushing','Teeth brushing','Shaving','Face washing',
    'Basic stretching','Posture awareness','Sitting still','Standing for long periods',
    'Walking on flat ground','Walking on stairs','Lifting light objects','Carrying groceries',
    'Opening jars','Tying knots','Using keys','Locking doors','Alarm clock use',
    'Phone calling','Text messaging','Email basics','Web browsing','Printer use',
    'Alarm setting','Calendar use','Clock reading','Basic time management',
    'Queue waiting','Polite greeting','Saying please/thank you','Apologizing',
    'Small talk','Active listening','Basic conversation','Table manners',
    'Punctuality','Hygiene maintenance','Weather appropriate dressing',
    'Shoe tying','Umbrella use','Public transport use','Ticket purchasing',
    'Basic directions','Crossing roads safely','Bicycle riding','Walking (endurance)',
    'Stretching (basic)','Resting effectively','Posture correction',
    'Stair climbing','Balance (basic)','Stooping','Kneeling','Crouching',
]:
    SKILLS.append(skill(n, random.choice(ST), C, f'Able to {n.lower()}.'))

# Social / interaction
for n in [
    'Introducing oneself','Remembering names','Thanking others','Complimenting',
    'Sympathy expression','Apologizing sincerely','Listening without interrupting',
    'Making eye contact','Reading facial expressions','Tone interpretation',
    'Friendly wave','Nodding affirmatively','Head shaking negatively',
    'Showing gratitude','Basic negotiation','Requesting help','Offering help',
    'Declining politely','Excusing oneself','Waiting turn to speak',
    'Basic conflict avoidance','Empathy (basic)','Patience (waiting)',
]:
    SKILLS.append(skill(n, 'charisma', C, f'Able to {n.lower()}.'))

# Physical basics (not inherent — learned coordination)
for n in [
    'Jumping (two feet)','Hopping (one foot)','Skipping','Galloping',
    'Crawling','Rolling (log roll)','Cartwheel (basic)','Somersault (basic)',
    'Catch (medium ball)','Throw (underhand)','Throw (overhand)','Kicking (stationary ball)',
    'Bouncing a ball','Dribbling (basic)','Tossing','Catching (small object)',
    'Balancing on one foot','Walking backwards','Walking on toes','Walking on heels',
    'Side shuffle','Cross step','Pivot turn','Jumping jacks',
    'Push-up (knee)','Sit-up','Plank (basic)','Squat','Lunge','Bridge (basic)',
    'Arm circles','Leg swings','Hip rotation','Shoulder roll','Neck stretch',
    'Wrist circles','Ankle circles','Finger tapping','Hand clapping',
    'Ladder climbing','Rope climbing (basic)','Rock scrambling','Beach walking',
    'Water wading','Paddling (pool)','Treading water','Doggy paddle','Floating (back)',
    'Floating (front)','Breath holding (30s)','Water treading','Splashing',
    'Jumping into water','Opening eyes underwater','Swimming (basic)',
    'Swimming (breaststroke)','Swimming (freestyle)','Floating on back',
]:
    SKILLS.append(skill(n, random.choice(['agility','endurance','strength','luck']), C, f'Able to {n.lower()}.'))

# Hobbies (common)
for n in [
    'Drawing (stick figures)','Coloring','Painting (basic)','Finger painting',
    'Clay modeling (basic)','Origami (basic)','Paper folding','Scissor cutting',
    'Glue application','Tape usage','Sticker placing','Puzzle assembly',
    'Jigsaw puzzle (100pc)','Maze solving','Dot-to-dot','Crossword (easy)',
    'Word search','Sudoku (easy)','Card shuffling','Card dealing',
    'Dice rolling','Board game rules','Card game rules','Dominoes',
    'Checkers','Chess (basic rules)','Draughts','Snakes and ladders',
    'Bingo','Lottery ticket filling','Coin flipping','Rock paper scissors',
    'Singing (casual)','Humming','Whistling','Rhythm clapping','Dancing (casual)',
    'Ballroom (basic steps)','Line dancing','Party dancing','Air guitar',
    'Air drumming','Finger snapping','Beatboxing (basic)','Karaoke',
    'Gardening (basic)','Weeding','Watering plants','Plant potting','Seed planting',
    'Leaf raking','Flower arranging','Composting basics','Bird watching',
    'Star gazing','Cloud watching','Fishing (basic)','Picnic preparation',
    'Campfire building','Tent setup (basic)','Hiking (easy trails)','Nature walking',
    'Photography (phone)','Selfie taking','Video recording (phone)','Social media posting',
    'Photo filtering','Hashtag use','Story posting','Meme sharing',
    'Petting animals','Dog walking','Cat care','Animal feeding','Fish tank care',
    'Insect observation','Bug collecting',
]:
    SKILLS.append(skill(n, random.choice(['intelligence','luck','charisma']), C, f'Able to {n.lower()}.'))

# Fill remaining common slots
common_extra = [
    'Map reading (basic)','Sign reading','Menu reading','Receipt checking',
    'Coin counting','Bill sorting','Change making','Tip calculating',
    'Phone book use','Address writing','Envelope addressing','Stamp licking',
    'Package wrapping','Gift bow tying','Card writing','Invitation making',
    'Candle lighting','Match striking','Fire starting (camp)','Charcoal lighting',
    'Grill operating','Kettle use','Toaster use','Microwave use',
    'Oven use (basic)','Stovetop use (basic)','Refrigerator organizing','Freezer use',
    'Can opening','Bottle opening','Cork removal','Food storage',
    'Leftover wrapping','Expiration checking','Produce washing','Knife handling (basic)',
    'Peeling vegetables','Chopping (basic)','Measuring ingredients','Mixing bowls',
    'Baking (basic)','Boiling water','Frying (basic)','Steaming (basic)',
    'Brewing tea','Coffee making (basic)','Juice pouring','Toast making',
    'Sandwich assembly','Salad making','Soup heating','Plate carrying',
    'Tray balancing','Table setting','Napkin folding','Glass filling',
    'Toast raising','Polite chewing','Napkin use','Elbow off table',
    'Serving others','Refilling drinks','Passing dishes','Clearing plates',
    'Leftover packing','Dish drying','Counter wiping','Sponge using',
    'Scrub brush use','Drain unclogging (basic)','Plunger use','Light bulb changing',
    'Battery replacement','Fuse checking','Tape measure use','Level use',
    'Hammer use (basic)','Screwdriver use (basic)','Pliers use','Wrench use (basic)',
    'Allen key use','Scissors use','Cutter use','Sandpaper use',
    'Paint brush use','Paint roller use','Masking tape use','Drop cloth laying',
    'Ladder setup (basic)','Step stool use','Furniture moving','Box carrying',
    'Bag carrying','Backpack packing','Suitcase packing','Zipper use',
    'Button fastening','Snap fastening','Lace tying','Belt buckling',
    'Watch wearing','Jewelry clasping','Glasses cleaning','Sunglass use',
    'Hat wearing','Scarf wrapping','Glove putting on','Jacket zipping',
    'Boot lacing','Sandal buckling','Snow boot wearing','Raincoat use',
    'Pocket use','Wallet carrying','Key organization','Phone holding',
    'Lanyard use','ID badge display','Name tag wearing','Badge scanning',
    'Turnstile use','Elevator use','Escalator riding','Door holding',
    'Door opening (push)','Door opening (pull)','Revolving door use','Window opening',
    'Blind adjusting','Curtain drawing','Lock checking','Deadbolt use',
    'Chain lock use','Peephole use','Intercom use','Buzzer pressing',
    'Gate lat ching','Fence climbing (low)','Gate opening','Path following',
    'Sidewalk walking','Curb stepping','Puddle avoiding','Stair railing use',
    'Ramp walking','Bridge crossing','Tunnel walking','Underpass use',
    'Crosswalk use','Traffic light reading','Pedestrian signaling','Car door opening',
    'Seat belt use','Seat adjustment','Mirror adjustment','Window rolling',
    'Door locking (car)','Car unlocking','Trunk opening','Hood release',
    'Gas cap opening','Gas pump use','Tire pressure check','Windshield cleaning',
    'Jump start cables','Jack use','Spare tire access','Hazard light use',
    'Horn use','Turn signal use','Headlight operation','Wiper use',
    'Defroster use','Heater use','AC use','Radio use',
    'AUX cord use','Bluetooth pairing','USB charging','Cigarette lighter use',
    'Cup holder use','Glove box use','Sun visor use','Rearview use',
    'Parallel parking (basic)','Three point turn','Lane change','Speed maintenance',
    'Stop sign obeying','Traffic light obeying','Yield sign obeying','Pedestrian yielding',
    'School zone slowing','Railroad crossing','Roundabout navigation','Merge (basic)',
    'Highway entry','Highway exit','Toll booth use','EZ pass use',
    'Parking brake use','Hill start','Wet road driving','Night driving (basic)',
    'Fog light use','Hazardous weather driving','Road flare use','Emergency kit use',
    'Basic defensive driving','Fuel efficiency driving','City navigation','Rural driving',
    'Driving (automatic)','Driving (manual basic)','Reverse driving','Tight space parking',
    'Snow chain installation','Ice scraper use','Windshield cover use','Antifreeze check',
    'Oil check','Coolant check','Brake fluid check','Wiper fluid fill',
    'Tire inflation','Air compressor use','Pressure gauge use','Tire tread check',
]
for n in common_extra:
    SKILLS.append(skill(n, random.choice(['endurance','strength','agility','intelligence']), C, f'Able to {n.lower()}.'))

# ── UNCOMMON (≈300) ────────────────────────────────────────────
U = 'uncommon'
uncommon_skills = [
    # Domestic (advanced)
    'Advanced cooking','Baking (advanced)','Pastry making','Bread baking',
    'Cake decorating','Knife skills (advanced)','Butchering','Fish cleaning',
    'Meat preparation','Vegetable carving','Food plating','Wine pairing',
    'Meal planning','Batch cooking','Food preservation','Canning',
    'Pickling','Fermenting','Cheese making','Brewing beer',
    'Home brewing basics','Wine making basics','Kombucha making','Sourdough starter',
    'Advanced cleaning','Deep cleaning','Carpet shampooing','Window cleaning',
    'Upholstery cleaning','Leather care','Wood polishing','Silver polishing',
    'Stain removal','Mold removal','Grout cleaning','Pressure washing',
    'Decluttering','Organizing (KonMari)','Space optimization','Wardrobe organizing',

    # Fitness / athletic
    'Running (5k)','Running (10k)','Jogging','Sprinting','Hurdling',
    'Long jump','High jump','Shot put','Discus throw','Javelin throw',
    'Pull-up','Chin-up','Dip','Muscle-up','Handstand',
    'Handstand walk','Cartwheel (advanced)','Back handspring','Front handspring',
    'Round-off','Aerial cartwheel','Tuck jump','Pike jump',
    'Lifting (gym)','Bench press','Squat (barbell)','Deadlift','Overhead press',
    'Clean and jerk','Snatch','Power clean','Kettlebell swing','Turkish get-up',
    'Calisthenics','Pistol squat','Human flag','Front lever','Back lever',
    'Planche (basic)','L-sit','V-sit','Skin the cat','Clapping push-up',
    'One arm push-up','Handstand push-up','Muscle-up (rings)','Ring dip',
    'Rope climb (advanced)','Pole climb','Tree climb (advanced)','Wall climb',
    'Free running','Precision jumping','Quadrupedal movement','Animal flow',
    'Yoga (intermediate)','Sun salutation','Downward dog','Warrior pose',
    'Tree pose','Triangle pose','Crow pose','Headstand','Shoulder stand',
    'Plow pose','Bridge pose','Wheel pose','Split (forward)','Split (side)',
    'Pilates','Barre','Dance (intermediate)','Ballet (basic)','Tap (basic)',
    'Jazz dance','Hip hop dance','Contemporary dance','Swing dance','Salsa (basic)',
    'Tango (basic)','Waltz (basic)','Foxtrot','Cha cha','Rumba',

    # Swimming / water sports (advanced)
    'Swimming (butterfly)','Swimming (backstroke)','Swimming (sidestroke)',
    'Diving (basic)','Diving (board)','Snorkeling','Free diving (10m)',
    'Surfing (basic)','Body surfing','Paddle boarding','Kayaking (basic)',
    'Canoeing (basic)','Rowing (basic)','Sailing (basic)','Boating (basic)',
    'Anchoring','Dock tying','Boat maintenance (basic)','Life jacket use',
    'Buoyancy control','Mask clearing','Snorkel clearing','Fin swimming',
    'Underwater swimming','Pool rescue basics','Throw bag use','Reach rescue',

    # Mechanical / technical
    'Bike maintenance','Flat tire repair','Chain lubrication','Brake adjustment',
    'Gear adjustment','Wheel truing','Bike assembly','Scooter repair',
    'Sewing machine use','Pattern reading','Fabric cutting','Garment sewing',
    'Zipper replacement','Button sewing','Hem adjustment','Patch application',
    'Knitting','Crocheting','Embroidery (basic)','Cross stitch','Weaving (basic)',
    'Macrame','Leather working (basic)','Leather stitching','Belt making',
    'Basic electrical','Plug replacement','Switch replacement','Socket replacement',
    'Fuse box operation','Circuit breaker reset','Wire stripping','Soldering (basic)',
    'Multimeter use','Voltage testing','Wire connection','Cable management',
    'Basic plumbing','Faucet repair','Toilet repair','Drain snaking',
    'Pipe insulation','Washer replacement','Valve operation','Water shut-off',
    'Basic carpentry','Saw use (hand)','Saw use (power)','Drill use',
    'Sander use','Router use','Jigsaw use','Circular saw use',
    'Wood measuring','Wood cutting','Nail hammering','Screw driving',
    'Wood jointing','Doweling','Wood gluing','Clamp use',
    'Sandpaper grading','Wood staining','Varnish application','Paint application',
    'Crack filling','Putty application','Caulking','Weather stripping',

    # Professional / knowledge
    'First aid (certified)','CPR','Heimlich maneuver','Wound dressing','Splint application',
    'Burn treatment','Fracture stabilization','Sprain wrapping','Shock management',
    'Bleeding control','Tourniquet use','AED use','Recovery position',
    'Emergency call procedure','Triage basics','Poison control','Allergy response',
    'EPI pen use','Asthma attack response','Stroke recognition','Heart attack recognition',
    'Typing (40wpm)','Touch typing','Word processing','Spreadsheet basics',
    'Presentation creation','Form filling','Data entry','File organization',
    'Filing system','Document scanning','Photocopier use','Fax machine use',
    'Bookkeeping basics','Receipt tracking','Invoice generation','Payment processing',
    'Cash handling','POS system use','Point of sale','Customer service',
    'Sales (basic)','Retail skills','Inventory counting','Stocking shelves',
    'Price tagging','Barcode scanning','Returns processing','Exchange handling',
    'Retail math','Merchandising','Visual display','Store opening',
    'Store closing','Security tag removal','Loss prevention basics',

    # Language / communication
    'Public speaking (basic)','Presentation skills','Group discussion','Debate (basic)',
    'Interview skills','CV writing','Cover letter writing','Email etiquette',
    'Business correspondence','Report writing','Minute taking','Agenda setting',
    'Meeting facilitation','Team coordination','Project coordination','Task delegation',
    'Deadline management','Prioritization','Multi-tasking','Time blocking',
    'Foreign language (basic)','Translation (basic)','Interpretation (basic)',
    'Sign language (basic)','Lip reading (basic)','Non-verbal communication',
    'Assertiveness training','Conflict resolution (basic)','Mediation (basic)',
    'Negotiation (intermediate)','Persuasion (intermediate)','Influence (basic)',

    # Knowledge domains
    'History (basic)','Geography (basic)','Politics (basic)','Economics (basic)',
    'Psychology (basic)','Sociology (basic)','Philosophy (basic)','Anthropology (basic)',
    'Biology (basic)','Chemistry (basic)','Physics (basic)','Astronomy (basic)',
    'Geology (basic)','Meteorology (basic)','Oceanography (basic)','Ecology (basic)',
    'Botany (basic)','Zoology (basic)','Anatomy (basic)','Nutrition (basic)',
    'Mathematics (basic)','Statistics (basic)','Probability (basic)','Logic (basic)',

    # Creative (intermediate)
    'Drawing (intermediate)','Sketching','Portrait drawing','Figure drawing',
    'Landscape drawing','Perspective drawing','Shading','Cross-hatching',
    'Watercolor painting','Acrylic painting','Oil painting','Pastel drawing',
    'Charcoal drawing','Ink drawing','Pen and ink','Calligraphy (basic)',
    'Hand lettering','Graffiti art','Mural painting','Spray paint art',
    'Digital painting','Pixel art','Vector art','Graphic design (basic)',
    'Photoshop (basic)','Photo editing (basic)','Video editing (basic)','Animation (basic)',
    'Pottery (basic)','Wheel throwing','Hand building','Clay sculpting',
    'Stone carving (basic)','Wood carving (basic)','Soap carving','Ice carving',
    'Metal working (basic)','Jewelry making (basic)','Beading','Wire wrapping',
    'Glass blowing (basic)','Stained glass (basic)','Mosaic making','Tile setting',
    'Music (basic)','Guitar (basic)','Piano (basic)','Drums (basic)',
    'Violin (basic)','Flute (basic)','Trumpet (basic)','Voice training (basic)',
    'Music reading','Tab reading','Chord playing','Rhythm keeping',
    'Song writing (basic)','Composition (basic)','Arrangement (basic)','Recording (basic)',
    'Audio editing (basic)','Mixing (basic)','Mastering (basic)','DJ (basic)',
    'Acting (basic)','Improvisation (basic)','Character creation','Scene work',
    'Monologue','Dialogue','Stage presence','Voice projection',
    'Body language acting','Emotional recall','Method acting (basic)','Script reading',
    'Photography (intermediate)','Composition','Lighting','Portrait photography',
    'Landscape photography','Street photography','Macro photography','Night photography',
    'Film photography','Darkroom developing','Film development','Print making',
    'Creative writing','Poetry','Short story','Essay writing',
    'Journalism (basic)','Article writing','Blogging','Copywriting',
    'Editing (text)','Proofreading','Fact checking','Research (basic)',
    'Library navigation','Database searching','Interviewing','Survey creation',
]

for n in uncommon_skills:
    SKILLS.append(skill(n, random.choice(['agility','endurance','strength','intelligence','charisma','luck']), U, f'Able to {n.lower()}.'))

# ── RARE (≈160) ─────────────────────────────────────────────────
R = 'rare'
rare_skills = [
    # Combat / martial arts
    'Martial arts (basic)','Karate (intermediate)','Judo (intermediate)','Aikido (basic)',
    'Taekwondo (intermediate)','Kung fu (basic)','Muay Thai (basic)','Boxing (intermediate)',
    'Kickboxing','Wrestling (intermediate)','Brazilian Jiu Jitsu (basic)','Krav Maga (basic)',
    'Capoeira (basic)','Fencing (basic)','Kendo (basic)','Archery (intermediate)',
    'Knife fighting (basic)','Staff fighting','Bo staff','Nunchaku',
    'Tonfa','Escrima sticks','Defensive tactics','Pressure points',
    'Disarming techniques','Grappling (intermediate)','Ground fighting','Submission holds',
    'Self defense (advanced)','Crowd control','Multiple opponent defense','Weapon retention',

    # Firearms / tactical
    'Firearms (intermediate)','Pistol marksmanship','Rifle marksmanship','Shotgun handling',
    'Tactical reload','Speed reload','Malfunction clearance','Weapon maintenance',
    'Cleaning (firearm)','Field strip','Zeroing','Ballistics (basic)',
    'Cover and concealment','Movement under fire','Room clearing (basic)','Team tactics (basic)',
    'Squad formations','Fire and maneuver','Bound and cover','Suppressive fire',
    'Ambush tactics','Counter ambush','Patrol techniques','Observation post',
    'Sniper (basic)','Spotting','Range estimation','Wind reading',
    'Night shooting','Low light tactics','Flashlight technique','Laser aiming',

    # Medical (advanced)
    'Suturing','Stapling','Incision','Drain placement','Catheterization',
    'Intubation','Airway management','Ventilator setup','IV insertion','Blood draw',
    'Medication administration','Dosage calculation','Drug identification','Triage (advanced)',
    'Trauma assessment','Head injury assessment','Chest decompression','Cricothyrotomy',
    'Emergency childbirth','Burn debridement','Amputation (emergency)','Field surgery (basic)',
    'Diagnosis (basic)','Symptom analysis','Medical history taking','Physical examination',
    'Lab test interpretation','X-ray reading (basic)','Ultrasound (basic)','EKG reading',
    'Anatomy (advanced)','Physiology (advanced)','Pathology (basic)','Pharmacology (basic)',
    'Veterinary care (basic)','Animal diagnosis','Animal surgery (basic)','Livestock care',
    'Herbal medicine (basic)','Tincture making','Salve preparation','Essential oil use',

    # Technical / engineering
    'Mechanical engineering (basic)','Engine repair','Transmission repair','Hydraulic systems',
    'Pneumatic systems','Welding (arc)','Welding (MIG)','Welding (TIG)',
    'Cutting torch','Brazing','Soldering (advanced)','Sheet metal work',
    'Machining (lathe)','Machining (mill)','CNC operation (basic)','3D printing',
    'Laser cutting','Water jet cutting','PLC programming (basic)','Robotics (basic)',
    'Automotive repair (intermediate)','Engine diagnostics','Brake replacement','Suspension work',
    'Exhaust system','Transmission work','Clutch replacement','Timing belt',
    'Head gasket','Electrical system (auto)','Battery systems','Alternator repair',
    'Starter repair','AC recharge','Tire mounting','Wheel balancing',
    'Alignment (basic)','Diagnostic code reading','OBD scan','Emission testing',

    # Electronics / computing
    'Computer assembly','Component identification','Motherboard repair','GPU repair',
    'Power supply repair','RAM installation','SSD installation','Thermal paste application',
    'Operating system install','Windows (advanced)','Linux (basic)','MacOS (advanced)',
    'Dual boot setup','Virtual machine setup','Network configuration','Router setup',
    'Firewall configuration','Network security (basic)','VPN setup','Proxy configuration',
    'Command line (basic)','Bash scripting','Batch scripting','PowerShell (basic)',
    'Programming (basic)','Python (basic)','JavaScript (basic)','HTML/CSS (basic)',
    'SQL (basic)','Database management (basic)','Web development (basic)','App development (basic)',
    'Hacking (basic)','Penetration testing (basic)','Vulnerability scanning','Password cracking',
    'Social engineering (basic)','Phishing identification','Encryption (basic)','Network mapping',
    'WiFi security','Bluetooth security','RFID cloning','Lock picking (basic)',
    'Safe cracking (basic)','Bypass techniques','Alarm bypass (basic)','Surveillance (basic)',
    'Counter surveillance','Bug sweeping','Debugging (electronic)','Reverse engineering (basic)',

    # Specialist knowledge
    'Chemistry (intermediate)','Organic chemistry','Inorganic chemistry','Biochemistry (basic)',
    'Analytical chemistry','Lab safety','Chemical synthesis','Compound identification',
    'Physics (intermediate)','Classical mechanics','Thermodynamics','Electromagnetism',
    'Quantum physics (basic)','Relativity (basic)','Nuclear physics (basic)','Optics (basic)',
    'Astronomy (intermediate)','Telescope operation','Celestial navigation','Orbital mechanics',
    'Geology (intermediate)','Rock identification','Mineral identification','Fossil identification',
    'Meteorology (intermediate)','Weather prediction','Cloud identification','Storm tracking',
    'Biology (intermediate)','Microbiology','Genetics (basic)','Ecology (intermediate)',
    'Marine biology','Forensic science (basic)','Evidence collection','Crime scene processing',
    'Fingerprint analysis','DNA collection','Toxicology (basic)','Ballistics analysis',
    'Legal knowledge (basic)','Criminal law basics','Constitutional law','Contract review',
    'Business law','Accounting (intermediate)','Tax preparation','Audit basics',
    'Financial analysis','Investment (basic)','Stock trading (basic)','Risk assessment',

    # Creative (advanced)
    'Musical instrument (intermediate)','Guitar (advanced)','Piano (intermediate)',
    'Violin (intermediate)','Drums (intermediate)','Saxophone (basic)','Trumpet (intermediate)',
    'Classical singing','Opera (basic)','Choir','Harmony singing',
    'Music production','DAW operation','MIDI sequencing','Sound design (basic)',
    'Live sound engineering','PA system setup','Monitor mixing','Feedback control',
    'Acting (intermediate)','Stage acting','Screen acting','Voice acting',
    'Theater production','Stage combat','Fight choreography','Stunt work (basic)',
    'Directing (basic)','Script writing (screen)','Play writing','Storyboarding',
    'Cinematography (basic)','Camera operation','Lighting for film','Grip work',
    'Film editing (intermediate)','Color grading','Sound editing','VFX (basic)',
    'Animation (intermediate)','2D animation','3D animation (basic)','Stop motion',
    'Game design (basic)','Level design','Game mechanics','Narrative design',

    # Extreme / adventure
    'Mountaineering (basic)','Rock climbing (intermediate)','Ice climbing (basic)',
    'Technical climbing','Rappelling','Belaying','Anchor building','Crampon use',
    'Ice axe use','Crevasse rescue','Glacier travel','Avalanche awareness',
    'Backcountry skiing','Cross country skiing','Snowboarding (intermediate)','Winter survival',
    'Whitewater rafting','Kayaking (intermediate)','Canoeing (intermediate)','Swift water rescue',
    'SCUBA diving (certified)','Deep diving (30m)','Night diving','Wreck diving',
    'Navigational diving','Dive buddy procedures','Decompression management','Nitrox use',
    'Hang gliding (basic)','Paragliding (basic)','Skydiving (basic)','BASE jumping (basic)',
    'Wingsuit flying (basic)','Zip line operations','High line walking','Rope bridge crossing',

    # Survival / outdoors
    'Survival (intermediate)','Primitive shelter','Debris shelter','Snow cave','Lean-to',
    'Fire by friction','Bow drill','Hand drill','Flint and steel','Fire piston',
    'Water purification','Water sourcing','Food foraging','Edible plant identification',
    'Mushroom identification','Trapping (basic)','Snare setting','Deadfall trap',
    'Spear fishing','Fishing (advanced)','Net fishing','Ice fishing',
    'Hunting (basic)','Tracking (basic)','Game trailing','Stalking',
    'Skinning','Butchering (wild game)','Hide tanning','Bone tool making',
    'Navigation (intermediate)','Map and compass','Terrain association','Dead reckoning',
    'GPS operation','Topographic map reading','Coordinates','Triangulation',
    'Orienteering','Night navigation','Urban navigation','Subterranean navigation',
    'Primitive tool making','Stone tool knapping','Bow making','Arrow making',
    'Spear making','Cordage making','Rope making','Basket weaving',
    'Pottery (functional)','Clay firing','Klin building','Charcoal making',
    'Natural medicine','Medicinal plant ID','First aid (wilderness)','Emergency shelter',
    'Signal building','Signal fire','Ground signals','Signal mirror',
]

for n in rare_skills:
    SKILLS.append(skill(n, random.choice(['strength','agility','endurance','intelligence','charisma','luck']), R, f'Able to {n.lower()}.'))

# ── VERY RARE (≈100) ────────────────────────────────────────────
VR = 'very_rare'
very_rare_skills = [
    'Special forces training','Counter terrorism','Hostage rescue','VIP protection',
    'Close protection (advanced)','Executive protection','Advance work','Route planning',
    'Risk assessment (security)','Threat evaluation','Intelligence gathering','Covert surveillance',
    'Undercover operations','Interrogation resistance','Escape and evasion','Evasion driving',
    'Combat driving','Off road driving (advanced)','Pursuit driving','Ram and block',
    'Aircraft pilot (private)','Helicopter pilot (basic)','Ultralight pilot','Glider pilot',
    'Commercial pilot (basic)','Instrument flying','Night flying','Emergency landing',
    'Combat shooting (advanced)','Tactical rifle','Close quarters battle','CQB room clearing',
    'Dynamic entry','Breaching','Ballistic shield','Sniper (intermediate)',
    'Counter sniper','Observations post','Target acquisition','Precision marksmanship',
    'Demolitions (basic)','Explosive placement','Blasting cap use','Det cord use',
    'Improvised explosives','Ordnance identification','Mine clearing','IED disposal (basic)',
    'Hacking (intermediate)','Network penetration','Web application testing','Wireless exploitation',
    'Binary exploitation','Reverse engineering (advanced)','Malware analysis','Cryptography (advanced)',
    'Social engineering (advanced)','Pretexting','Tailgating','Impersonation',
    'Safe cracking (advanced)','Lock manipulation','Safecracking (drill)','Vault entry',
    'Jewelry appraisal','Art appraisal','Antique identification','Forgery detection',
    'Counterfeit detection','Document forgery','Passport forgery','Signature forgery',
    'Neurosurgery (basic)','Cardiothoracic (basic)','Organ transplant (basic)','Anesthesiology',
    'Radiology (advanced)','Pathology (advanced)','Forensic pathology','Criminal profiling',
    'Nuclear engineering (basic)','Radiological safety','Hazmat handling','Decontamination',
    'Chemical engineering (basic)','Pharmaceutical synthesis','Toxin extraction','Antivenom production',
    'Professional diving (advanced)','Saturation diving','Commercial diving','Underwater welding',
    'Underwater demolition','Deep sea salvage','Submersible pilot','ROV operation',
    'High altitude mountaineering (8000m)','Extreme altitude survival','Cold weather warfare','Arctic survival',
    'Jungle survival','Desert survival','Maritime survival','Open ocean survival',
    'Aviation survival','Ejection seat survival','Parachute (advanced)','HALO jump',
    'Military freefall','HAHO jump','Combat skydiving','Insertion techniques',
    'Extraction techniques','Fast rope','Repelling (combat)','Helicopter insertion',
    'Combat medic','Special operations medic','Field surgery (advanced)','Trauma surgery (basic)',
    'Advanced interrogation','Psychological operations','Counterintelligence','Deception operations',
    'Signals intelligence','Communications security','Encryption (military)','Frequency hopping',
    'Lock picking (advanced)','Bypass (electronic)','Safe manipulation','Combination lock cracking',
    'Pickpocketing','Sleight of hand (advanced)','Prestidigitation','Stage magic (intermediate)',
    'Mentalism (basic)','Hypnosis (basic)','Memory techniques (advanced)','Speed reading',
    'Polyglot (5+ languages)','Translation (advanced)','Interpretation (simultaneous)','Cryptanalysis',
    'Kinesics','Microexpression reading','Statement analysis','Behavioral analysis',
    'Urban exploration (advanced)','Vertical climbing (buildings)','Industrial climbing','Rope access',
    'Stunt driving','Precision driving','J turn','Reverse 180',
    'Motorcycle (advanced)','Off road motorcycle','Enduro racing','Motocross',
    'Advanced martial arts','Multiple disciplines','Weapons master (basic)','Firearms (expert)',
    'Tactical emergency medicine','Combat casualty care','Tactical combat casualty care','Prolonged field care',
    'Nuclear biological chemical defense','CBRN operations','Decontamination (advanced)','Radiological monitoring',
]

for n in very_rare_skills:
    SKILLS.append(skill(n, random.choice(['strength','agility','endurance','intelligence','charisma','luck','psyche_force']), VR, f'Able to {n.lower()}.'))

# ── LEGENDARY (≈40) ─────────────────────────────────────────────
L = 'legendary'
legendary_skills = [
    'Photographic memory','Eidetic recall','Total recall','Perfect pitch',
    'Absolute pitch','Synesthesia (cognitive)','Hyperthymesia','Calculating prodigy',
    'Speed reader (1000 wpm)','Blindfold chess','Mental abacus','Lightning calculator',
    'Savant calculation','Calendar calculation','Polyglot (10+ languages)','Hyperpolyglot',
    'Master surgeon','Neurosurgeon (advanced)','Cardiothoracic surgeon','Transplant surgeon',
    'Expert pilot (all fixed wing)','Helicopter (advanced)','Jet fighter (basic)','Aerobatic pilot',
    'Combat shooting (legendary)','Quick draw','Trick shooting','No look shooting',
    'Zen archery','Instinctive archery','Master martial artist','Multiple style master',
    'Weapon master (advanced)','Kali/Eskrima master','Iaido master','Kendo master',
    'Master of disguise','Master of impersonation','Master of escape','Houdini-like escape',
    'Master lockpicker','Master safecracker','Master forger','Master counterfeiter',
    'Master of sleight of hand','Stage magic (advanced)','Grand illusion','Mentalism (advanced)',
    'Hypnosis (advanced)','Mass hypnosis','Instant hypnotic induction','Deep trance induction',
    'Master tracker','Master hunter','Master survivalist','Primitive technology expert',
    'Master navigator','Polynesian navigation','Celestial navigation (expert)','Dead reckoning (expert)',
    'Master chef','Master sommelier','Master perfumer','Master distiller',
    'Master artist','Master painter','Master sculptor','Master musician',
    'Composer (symphonic)','Conductor','Virtuoso instrumentalist','Virtuoso pianist',
    'Virtuoso violinist','Virtuoso guitarist','Master watchmaker','Master gunsmith',
    'Master armorer','Master bowyer','Master swordsmith','Master blacksmith',
    'Polyhistor (polymath)','Renaissance mind','Expert generalist','Universal scholar',
    'Master tactician','Grandmaster strategist','Chess grandmaster','Go master',
    'Combat intuition','Situational awareness (supernatural)','Danger sense (instinctive)',
    'Predator instinct','Killing intent sensing','Lie detection (expert)','Human lie detector',
    'Cold reading (expert)','Hot reading','Psychological insight (deep)','Character assessment',
    'Pain tolerance (exceptional)','Cold resistance (exceptional)','Heat resistance (exceptional)',
    'Deprivation tolerance','Sleep deprivation resistance','Starvation resistance',
    'Fear suppression','Adrenaline control','Pain suppression','Bleeding control (exceptional)',
    'Healing factor (accelerated)','Disease resistance','Toxin resistance','Poison resistance',
    'Pressure resistance','Extreme environment adaptation','High G tolerance','Hypoxia tolerance',
]

for n in legendary_skills:
    SKILLS.append(skill(n, random.choice(['strength','agility','endurance','intelligence','charisma','luck','psyche_force']), L, f'{n.lower()}.', cap=22))

# ════════════════════════════════════════════════════════════════
# WEAKNESSES — 200 total
# ════════════════════════════════════════════════════════════════
# rarity → population frequency:
#   common:   ~30%  (≈60 weaknesses)
#   uncommon: ~15%  (≈50)
#   rare:     ~5%   (≈40)
#   very_rare: ~1%  (≈30)
#   legendary: <0.1% (≈20)

# ── COMMON WEAKNESSES (≈60) ────────────────────────────────────
for n in [
    'Clumsy','Forgetful','Impatient','Gullible','Naive','Indecisive',
    'Pessimistic','Cynical','Blunt','Tactless','Nosy','Gossip',
    'Loud','Messy','Disorganized','Procrastinator','Lazy (mild)','Stubborn',
    'Argumentative','Whiny','Complainer','Bitter','Grudge holder','Jealous (mild)',
    'Vain','Show-off','Humble to a fault','Over-apologetic','People pleaser',
    'Overthinker','Worrier','Anxious (mild)','Self-critical','Perfectionist',
    'Imposter syndrome','Stage fright (mild)','Fear of heights (mild)','Fear of spiders (mild)',
    'Fear of snakes (mild)','Fear of flying (mild)','Fear of public speaking (mild)','Fear of darkness (mild)',
    'Fear of enclosed spaces (mild)','Fear of open water (mild)','Fear of needles (mild)','Fear of blood (mild)',
    'Fear of germs (mild)','Fear of animals (mild)','Fear of crowds (mild)','Fear of strangers (mild)',
    'Nail biting','Hair twirling','Knuckle cracking','Lip biting',
    'Skin picking','Scab picking','Nose picking','Thumb sucking',
    'Nail picking','Cuticle biting','Pencil chewing','Straw bending',
    'Whistling (nervous)','Humming (nervous)','Leg bouncing','Tapping (nervous)',
    'Pacing','Checking (repeated)','Hoarding (mild)','Collecting (excessive)',
    'Tardiness','Overpromising','Interrupting','Talking too much',
    'Oversharing','One-upping','Name dropping','Bragging',
    'Self-deprecating (excessive)','Avoiding confrontation','Avoiding eye contact','Mumbling',
    'Slouching','Poor posture','Fidgeting','Restlessness',
    'Pickiness (food)','Fussy eating','Picky eating','Food aversion',
    'Caffeine dependency','Sugar craving','Comfort eating','Snacking (excessive)',
    'Nail polish picking','Cuticle picking','Hair pulling (mild)','Cheek biting',
    'Hypervigilance (mild)','Startle reflex (high)','Jumpiness','Nervous laughter',
    'Skeptical (excessive)','Distrustful (mild)','Suspicious (mild)','Paranoid (mild)',
]:
    WEAKNESSES.append(weak(n, 'common', f'{n.lower()}.'))

# ── UNCOMMON WEAKNESSES (≈50) ──────────────────────────────────
for n in [
    'Asthma (mild)','Allergies (seasonal)','Allergies (food)','Allergies (dust)',
    'Allergies (pets)','Allergies (latex)','Allergies (medication)','Eczema',
    'Psoriasis','Acne (chronic)','Rosacea','Dandruff (severe)',
    'Back pain (chronic)','Neck pain (chronic)','Knee pain','Joint pain',
    'Carpal tunnel (mild)','Tendonitis','Plantar fasciitis','Flat feet',
    'Poor eyesight (corrected)','Color blindness (partial)','Astigmatism','Night blindness (mild)',
    'Tinnitus (mild)','Hearing loss (mild)','Vertigo (mild)','Motion sickness',
    'Migraines (occasional)','Tension headaches','Cluster headaches','Sinusitis (chronic)',
    'Insomnia (mild)','Sleepwalking','Nightmares (frequent)','Teeth grinding',
    'Sleep apnea (mild)','Restless leg syndrome','Narcolepsy (mild)','Fatigue (chronic)',
    'Depression (mild)','Anxiety disorder (mild)','Social anxiety (mild)','Panic attacks (occasional)',
    'PTSD (mild)','OCD (mild)','ADHD (mild)','Dyslexia','Dyscalculia','Dyspraxia',
    'Phobia (moderate)','Claustrophobia','Acrophobia','Agoraphobia','Arachnophobia',
    'Ophidiophobia','Cynophobia','Astraphobia','Trypophobia','Dental phobia',
    'Emetophobia','Coulrophobia','Trypanophobia','Hemophobia','Aerophobia',
    'Aquaphobia','Bathophobia','Monophobia','Gamophobia','Autophobia',
    'Alcohol dependency','Smoking addiction','Vaping addiction','Cannabis dependency',
    'Gambling habit','Shopping addiction','Social media addiction','Gaming addiction',
    'Poor sense of direction','Bad with names','Bad with faces','Bad with numbers',
    'Stage fright (moderate)','Writer\'s block','Creative block','Decision paralysis',
    'Overthinking (rumination)','Catastrophizing','Impostor syndrome (moderate)','Low self esteem',
    'People pleasing (compulsive)','Conflict avoidance (extreme)','Approval seeking',
]:
    WEAKNESSES.append(weak(n, 'uncommon', f'{n.lower()}.'))

# ── RARE WEAKNESSES (≈40) ──────────────────────────────────────
for n in [
    'Blind in one eye','Deaf in one ear','Partial hearing loss','Speech impediment (stutter)',
    'Speech impediment (lisp)','Voice disorder','Vocal cord damage (mild)','Cleft palate (repaired)',
    'Missing finger(s)','Missing toe(s)','Club foot (corrected)','Limb length discrepancy',
    'Scoliosis (moderate)','Spinal stenosis','Herniated disc','Degenerative disc disease',
    'Arthritis (chronic)','Rheumatoid arthritis','Osteoarthritis','Fibromyalgia',
    'Diabetes (type 1)','Diabetes (type 2)','Epilepsy','Seizure disorder',
    'Autoimmune disorder','Crohn\'s disease','Ulcerative colitis','IBS (severe)',
    'Thyroid disorder','Adrenal insufficiency','Hormonal imbalance','Pituitary disorder',
    'Heart condition (arrhythmia)','Heart murmur','Mitral valve prolapse','Cardiomyopathy',
    'High blood pressure (chronic)','Low blood pressure','POTS','Anemia (chronic)',
    'Sickle cell trait','Thalassemia','Hemophilia (mild)','Clotting disorder',
    'Asthma (severe)','COPD','Emphysema','Pulmonary fibrosis',
    'Kidney stones (recurring)','Kidney disease (mild)','Liver disease (mild)','Gallbladder issues',
    'Obesity (moderate)','Underweight (chronic)','Eating disorder (past)','Binge eating disorder',
    'Anorexia (recovered)','Bulimia (recovered)','ARFID','Orthorexia',
    'Phobia (severe)','Agoraphobia (moderate)','Claustrophobia (severe)','Acrophobia (severe)',
    'Social anxiety (moderate)','Panic disorder','Panic attacks (frequent)','Generalized anxiety',
    'Depression (major)','Persistent depressive disorder','Bipolar (type 2)','Cyclothymia',
    'PTSD (moderate)','Complex PTSD','OCD (moderate)','Hoarding disorder',
    'ADHD (moderate)','Autism spectrum (mild)','Asperger syndrome','Sensory processing disorder',
    'Tourette syndrome','Tic disorder','Trichotillomania','Dermatillomania',
    'Body dysmorphia','Dysmorphophobia','Eating disorder (active)','Substance dependency (prior)',
    'Alcoholism (recovering)','Opioid dependency (past)','Prescription dependency','Sedative dependency',
    'Chronic pain syndrome','Complex regional pain','Trigeminal neuralgia','Neuropathy',
    'Carpal tunnel (severe)','Tennis elbow (chronic)','Rotator cuff injury','Frozen shoulder',
    'Ankle instability','ACL tear (repaired)','Meniscus tear','Hip dysplasia',
    'Pelvis misalignment','Sciatica (chronic)','Piriformis syndrome','RSI (chronic)',
    'Vertigo (Meniere\'s)','Labyrinthitis','Vestibular disorder','Balance disorder',
    'Sun sensitivity','Cold sensitivity','Heat sensitivity','Chemical sensitivity',
    'Gluten intolerance','Lactose intolerance','Fructose malabsorption','Histamine intolerance',
]:
    WEAKNESSES.append(weak(n, 'rare', f'{n.lower()}.'))

# ── VERY RARE WEAKNESSES (≈30) ─────────────────────────────────
for n in [
    'Blindness (total)','Deafness (total)','Mutism','Quadriplegia',
    'Paraplegia','Hemiplegia','Monoplegia','Paralysis (partial)',
    'Missing arm','Missing leg','Missing hand','Missing foot',
    'Amputation (above knee)','Amputation (below knee)','Amputation (above elbow)','Amputation (below elbow)',
    'Multiple amputations','Spinal cord injury','Traumatic brain injury','Brain damage (moderate)',
    'Cerebral palsy','Muscular dystrophy','Multiple sclerosis','ALS (early)',
    'Parkinson\'s disease','Huntington\'s disease','Dementia (early onset)','Alzheimer\'s (early)',
    'Schizophrenia','Schizoaffective disorder','Bipolar (type 1)','Borderline personality disorder',
    'Antisocial personality disorder','Narcissistic personality disorder','Multiple personality disorder','Dissociative identity disorder',
    'Severe PTSD','PTSD (complex, severe)','Conversion disorder','Factitious disorder',
    'Body integrity dysphoria','Gender dysphoria (severe)','Psychotic episodes','Hallucinations (chronic)',
    'Delusional disorder','Paranoid schizophrenia','Catatonia','Agnosia',
    'Aphasia','Apraxia','Ataxia','Anosmia (complete)',
    'Ageusia (complete)','Analgesia (congenital)','CIPA','Proprioception loss',
    'Chronic fatigue syndrome (severe)','Fibromyalgia (severe)','Chronic Lyme disease','ME/CFS',
    'Organ failure (kidney)','Organ failure (liver)','Organ failure (heart)','Organ failure (lung)',
    'HIV/AIDS','Hepatitis C','Tuberculosis (active)','Leprosy',
    'Cancer (active)','Leukemia','Lymphoma','Brain tumor',
    'Severe autoimmune','Lupus (severe)','Scleroderma','Sjogren\'s syndrome',
    'Gigantism','Dwarfism','Progeria','Marfan syndrome',
    'Ehlers-Danlos','Epidermolysis bullosa','Ichthyosis','Albinism',
    'Amnesia (partial)','Amnesia (extensive)','Amnesia (complete)','Fugue state',
    'Aphantasia','Face blindness (prosopagnosia)','Alexia','Acalculia',
]:
    WEAKNESSES.append(weak(n, 'very_rare', f'{n.lower()}.'))

# ── LEGENDARY WEAKNESSES (≈20) ─────────────────────────────────
for n in [
    'Locked-in syndrome','Complete paralysis','Total locked-in','Full body paralysis',
    'Vegetative state','Minimally conscious state','Comatose','Brain death',
    'Total amnesia','Permanent amnesia','Global amnesia','Complete memory loss',
    'Catatonic schizophrenia','Severe catatonia','Complete dissociation','Total fugue state',
    'Fatal hereditary disease','Huntington\'s (active)','Familial Alzheimer\'s','Prion disease',
    'Degenerative brain disorder','CJD','Fatal insomnia','Motor neuron disease (advanced)',
    'Multiple organ failure','End stage organ failure','Total organ failure','Systematic organ failure',
    'Severe immunodeficiency','SCID','Bubble boy syndrome','Combined immunodeficiency',
    'Total aphasia','Complete language loss','Global aphasia','Total communication loss',
    'Quadruple amputation','Total limb loss','Complete dismemberment','Total body trauma',
    'Congenital analgesia (complete)','Congenital insensitivity to pain','Complete sensory loss','Total anesthesia',
]:
    WEAKNESSES.append(weak(n, 'legendary', f'{n.lower()}.'))

# ════════════════════════════════════════════════════════════════
# Ensure exactly 1000 skills, 200 weaknesses
# ════════════════════════════════════════════════════════════════
# Trim/pad skills to 1000 by rarity
def trim_rarity(items, target, ratios=None):
    """Trim list to target size preserving distribution ratios."""
    if ratios is None:
        ratios = {'legendary':4,'very_rare':10,'rare':16,'uncommon':30,'common':40}
    if len(items) <= target:
        return items
    tiers = {}
    for it in items:
        tiers.setdefault(it['rarity'], []).append(it)
    kept = []
    total_ratio = sum(ratios.values())
    for r in ['legendary','very_rare','rare','uncommon','common']:
        bucket = tiers.get(r, [])
        if not bucket: continue
        alloc = int(target * ratios[r] / total_ratio)
        leftover = target - len(kept)
        take = min(len(bucket), alloc, leftover)
        kept.extend(bucket[:take])
    if len(kept) < target:
        for r in ['legendary','very_rare','rare','uncommon','common']:
            for it in tiers.get(r, []):
                if it not in kept and len(kept) < target:
                    kept.append(it)
    return kept[:target]
SKILLS = trim_rarity(SKILLS, 1000)
WEAKNESSES = trim_rarity(WEAKNESSES, 200)
# Build combined pool, verify counts, write output
# ════════════════════════════════════════════════════════════════
pool = SKILLS + WEAKNESSES

# ── Verify numbers ─────────────────────────────────────────────
rarity_map = {'common':0,'uncommon':0,'rare':0,'very_rare':0,'legendary':0}
type_map = {'skill':0,'weakness':0}
for e in pool:
    rarity_map[e['rarity']] = rarity_map.get(e['rarity'],0)+1
    type_map[e['type']] = type_map.get(e['type'],0)+1

print(f'{"Total pool entries:":30s} {len(pool)}')
print(f'{"Skills:":30s} {type_map["skill"]}')
print(f'{"Weaknesses:":30s} {type_map["weakness"]}')
print(f'{"Common:":30s} {rarity_map["common"]}')
print(f'{"Uncommon:":30s} {rarity_map["uncommon"]}')
print(f'{"Rare:":30s} {rarity_map["rare"]}')
print(f'{"Very Rare:":30s} {rarity_map["very_rare"]}')
print(f'{"Legendary:":30s} {rarity_map["legendary"]}')
print(f'\nSkills by rarity:')
for r in ['common','uncommon','rare','very_rare','legendary']:
    c = sum(1 for s in SKILLS if s['rarity']==r)
    print(f'  {r:15s} {c}')
print(f'\nWeaknesses by rarity:')
for r in ['common','uncommon','rare','very_rare','legendary']:
    c = sum(1 for w in WEAKNESSES if w['rarity']==r)
    print(f'  {r:15s} {c}')

# ── Write output ────────────────────────────────────────────────
output = {
    '_note': 'Pool of 1000 skills + 200 weaknesses for character generation. '
             'type:"skill" = learned ability, type:"weakness" = debility. '
             'rarity controls draw probability. max is skill\'s human cap (19 = average max, 22 = prodigy).',
    'pool': pool
}
OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\nWritten to {OUT}')
