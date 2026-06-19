"""Seed interactive objects into canvas_map rooms. Safe to re-run — skips rooms that already have objects."""
import json

OBJECTS_BY_TYPE = {
    'train_station': [
        {'sfx':'blast-door',     'type':'door',       'emoji':'🚪','label':'Emergency Blast Door',  'state':'locked',     'x':0.05,'y':0.5, 'desc':'Heavy blast door sealing the train tunnel. Locked from outside during lockdown. The only route back to the surface.'},
        {'sfx':'ticket-terminal','type':'terminal',   'emoji':'🖥️','label':'Ticket Terminal',        'state':'active',     'x':0.72,'y':0.25,'desc':'Electronic kiosk. Screen reads: NEXT DEPARTURE SUSPENDED — FACILITY LOCKDOWN IN EFFECT. Last train departed 06:18.'},
        {'sfx':'supply-locker',  'type':'locker',     'emoji':'🧰','label':'Emergency Supply Locker','state':'unsearched', 'x':0.85,'y':0.72,'desc':'Wall-mounted emergency locker. Umbrella safety regulations require one per transit zone.'},
    ],
    'floor': [
        {'sfx':'security-terminal','type':'terminal', 'emoji':'🖥️','label':'Security Terminal',     'state':'active',     'x':0.82,'y':0.2, 'desc':'Active security console. Camera feeds, door lock controls — if you have the clearance.'},
        {'sfx':'stairwell-door',   'type':'door',     'emoji':'🚪','label':'Stairwell Door',         'state':'locked',     'x':0.5, 'y':0.95,'desc':'Emergency stairwell connecting B1 to B2. Sealed by lockdown. Needs a Level 2 keycard or bypass.'},
        {'sfx':'dead-guard',       'type':'body',     'emoji':'💀','label':'Dead Security Guard',    'state':'unsearched', 'x':0.35,'y':0.62,'desc':'Umbrella security officer. Throat torn out. His keycard may still be on him.'},
        {'sfx':'notice-board',     'type':'document', 'emoji':'📋','label':'Emergency Notice Board', 'state':'unsearched', 'x':0.18,'y':0.18,'desc':'Mounted bulletin board. Covered in evacuation procedures and internal memos about "containment of biohazard event".'},
    ],
    'checkpoint': [
        {'sfx':'keypad',          'type':'keypad',   'emoji':'🔒','label':'Security Keypad',        'state':'locked',     'x':0.12,'y':0.5, 'desc':'Biometric keypad controlling blast door access to B2. Requires Level 3 clearance or a skilled bypass.'},
        {'sfx':'guard-terminal',  'type':'terminal', 'emoji':'🖥️','label':'Guard Station Terminal', 'state':'active',     'x':0.72,'y':0.3, 'desc':'Checkpoint workstation. Personnel logs, access records, camera timestamps from the morning of the outbreak.'},
        {'sfx':'equipment-locker','type':'locker',   'emoji':'🧰','label':'Guard Equipment Locker', 'state':'unsearched', 'x':0.88,'y':0.7, 'desc':'Standard security locker. Contains equipment left behind when the guards abandoned their post.'},
        {'sfx':'security-log',    'type':'document', 'emoji':'📋','label':'Security Log',           'state':'unsearched', 'x':0.5, 'y':0.15,'desc':'Physical checkpoint logbook. Last entry: 06:09. "Unusual activity on sublevel B3. Dispatching team. All quiet."'},
    ],
    'corridor': [
        {'sfx':'fuse-box',     'type':'electrical','emoji':'⚡','label':'Fuse Box',              'state':'active',     'x':0.08,'y':0.5, 'desc':'Corridor power distribution box. Could cut or reroute power to specific sections of the facility.'},
        {'sfx':'intercom',     'type':'intercom',  'emoji':'📡','label':'Intercom Station',      'state':'active',     'x':0.92,'y':0.5, 'desc':'Wall-mounted intercom. Static on most channels. Something is breathing on channel 4.'},
        {'sfx':'dead-worker',  'type':'body',      'emoji':'💀','label':'Dead Maintenance Worker','state':'unsearched', 'x':0.5, 'y':0.5, 'desc':'Facility maintenance worker. Badly mauled. A keycard is visible under the body.'},
    ],
    'dining': [
        {'sfx':'kitchen-storage','type':'locker',   'emoji':'🧰','label':'Kitchen Storage',    'state':'unsearched', 'x':0.12,'y':0.5, 'desc':'Large pantry behind the serving counter. Canned goods, utensils, cleaning supplies. Some still usable.'},
        {'sfx':'dead-cook',     'type':'body',      'emoji':'💀','label':'Dead Cook',          'state':'unsearched', 'x':0.72,'y':0.7, 'desc':'Kitchen staff. Half-eaten. Whatever got her was mid-shift when it happened. She was still holding a ladle.'},
        {'sfx':'generator',     'type':'generator', 'emoji':'🔋','label':'Backup Generator',  'state':'inactive',   'x':0.88,'y':0.2, 'desc':'Emergency diesel generator. Fuel cell looks intact. Could restore power to this section if activated.'},
        {'sfx':'menu-board',    'type':'document',  'emoji':'📋','label':'Daily Menu Board',   'state':'unsearched', 'x':0.5, 'y':0.08,'desc':'Today\'s menu: Chicken Marsala, Garden Salad, Fruit Cup. Date stamps from the morning of the outbreak. Someone had a last meal here.'},
    ],
    'medical': [
        {'sfx':'med-cabinet',    'type':'med_cabinet', 'emoji':'💊','label':'Medical Supply Cabinet', 'state':'unsearched', 'x':0.18,'y':0.3, 'desc':'Umbrella standard medical cabinet. First aid kits, bandages, antiseptic, suture kits. Could restore HP.'},
        {'sfx':'drug-cabinet',   'type':'drug_cabinet','emoji':'💉','label':'Drug Cabinet',           'state':'locked',     'x':0.18,'y':0.72,'desc':'Locked narcotics cabinet. Contains pharmaceutical-grade painkillers and adrenaline stimulants — significant combat bonuses.'},
        {'sfx':'patient-terminal','type':'terminal',   'emoji':'🖥️','label':'Patient Records Terminal','state':'active',    'x':0.82,'y':0.3, 'desc':'Medical database. Team health records, injury reports. Also shows biometric data recorded during the outbreak.'},
        {'sfx':'dead-medic',     'type':'body',        'emoji':'💀','label':'Dead Medical Officer',    'state':'unsearched', 'x':0.6, 'y':0.72,'desc':'Umbrella field medic. Still clutching a half-filled syringe. Cause of death: self-inflicted. Her access badge is pinned to her coat.'},
    ],
    'lab': [
        {'sfx':'specimen-storage','type':'specimen',  'emoji':'🧬','label':'Specimen Storage Unit',  'state':'sealed',    'x':0.15,'y':0.5, 'desc':'Sealed containment unit for T-virus specimens. Warning labels in four languages. The seal is cracked — very slightly.'},
        {'sfx':'research-terminal','type':'terminal', 'emoji':'🖥️','label':'Research Terminal',      'state':'active',    'x':0.78,'y':0.28,'desc':'Main lab workstation. T-virus mutation logs, containment breach timeline, Project ALICE research notes.'},
        {'sfx':'dead-researcher', 'type':'body',      'emoji':'💀','label':'Dead Researcher',         'state':'unsearched','x':0.5, 'y':0.72,'desc':'Senior virologist. Died at her workstation. Research notes scattered around her. Her access badge is still around her neck.'},
        {'sfx':'biohazard-container','type':'hazard', 'emoji':'☣️','label':'Biohazard Containment Unit','state':'breached','x':0.88,'y':0.72,'desc':'Pressurised biological containment vessel. Seal is broken. Whatever was inside has been loose for hours. Do not approach without protection.'},
    ],
    'tunnels': [
        {'sfx':'toolbox',     'type':'locker',    'emoji':'🔧','label':'Maintenance Toolbox',  'state':'unsearched', 'x':0.18,'y':0.5, 'desc':'Heavy-duty tool kit. Bolt cutters, wirecutters, a wrench set. Useful for bypassing mechanical locks or cutting chains.'},
        {'sfx':'main-power',  'type':'electrical','emoji':'⚡','label':'Main Power Panel',     'state':'active',     'x':0.72,'y':0.28,'desc':'Central power distribution for the entire facility. Cutting it plunges everything — lights, locks, cameras — into darkness.'},
        {'sfx':'power-cell',  'type':'locker',    'emoji':'🔋','label':'Backup Power Cell',   'state':'unsearched', 'x':0.88,'y':0.72,'desc':'Portable power cell. Could restart a generator or power an offline terminal.'},
        {'sfx':'service-hatch','type':'door',     'emoji':'🚪','label':'Service Hatch',       'state':'unlocked',   'x':0.5, 'y':0.95,'desc':'Low crawlspace access hatch. Connects maintenance tunnels to the armory ventilation shaft. Uncomfortable but passable.'},
    ],
    'armory': [
        {'sfx':'weapon-rack',    'type':'weapon_rack', 'emoji':'🔫','label':'Weapon Rack',           'state':'partial',    'x':0.5, 'y':0.12,'desc':'Wall-mounted rack. Several weapons already taken. Two assault rifles and a combat shotgun remain, along with spare magazines.'},
        {'sfx':'ammo-cache',     'type':'locker',      'emoji':'🧰','label':'Ammunition Cache',      'state':'unsearched', 'x':0.18,'y':0.7, 'desc':'Heavy steel ammo crate. Mixed calibers. More than enough to resupply the whole team.'},
        {'sfx':'secured-locker', 'type':'locker',      'emoji':'🔒','label':'Secured Weapons Locker','state':'locked',     'x':0.88,'y':0.5, 'desc':'High-security armored locker. Requires Level 4 keycard. Whatever is inside, Umbrella did not want it easily accessible.'},
        {'sfx':'dead-soldier',   'type':'body',        'emoji':'💀','label':'Dead Umbrella Soldier',  'state':'unsearched', 'x':0.5, 'y':0.72,'desc':'Elite security unit. Something punched through his body armor. He still has his sidearm holstered.'},
    ],
    'containment': [
        {'sfx':'cell-panel',          'type':'keypad',  'emoji':'🔒','label':'Cell Control Panel',       'state':'broken',    'x':0.5, 'y':0.08,'desc':'Containment cell management interface. Shows all cells as BREACHED. Emergency locks were overridden from inside. Still shows cell occupant history.'},
        {'sfx':'dead-guard-2',        'type':'body',    'emoji':'💀','label':'Dead Containment Guard',   'state':'unsearched','x':0.82,'y':0.5, 'desc':'Guard stationed at the cell block. Signs of extreme trauma. His panic button was triggered but never answered.'},
        {'sfx':'containment-terminal','type':'terminal','emoji':'🖥️','label':'Containment Terminal',    'state':'active',    'x':0.18,'y':0.5, 'desc':'Specimen monitoring system. Shows former occupant biometrics and containment logs. All readings: flatlined — then offline.'},
        {'sfx':'specimen-cage',       'type':'hazard',  'emoji':'☣️','label':'Breached Specimen Cage',   'state':'breached',  'x':0.5, 'y':0.62,'desc':'Heavily reinforced cage. The door was torn off from the inside. Claw marks on the frame. Whatever was here is long gone.'},
    ],
    'cryogenic': [
        {'sfx':'cryo-pod-a',  'type':'cryo_pod', 'emoji':'❄️','label':'Cryo Pod A',          'state':'occupied',  'x':0.2, 'y':0.28,'desc':'Occupied. Biosigns faint but stable. Occupant in deep stasis. Revival is possible but carries risk — their condition is deteriorating.'},
        {'sfx':'cryo-pod-b',  'type':'cryo_pod', 'emoji':'❄️','label':'Cryo Pod B',          'state':'occupied',  'x':0.2, 'y':0.62,'desc':'Occupied. Biosigns stable. Occupant identity: CLASSIFIED. Red clearance badge visible through the frosted glass.'},
        {'sfx':'cryo-pod-c',  'type':'cryo_pod', 'emoji':'❄️','label':'Cryo Pod C',          'state':'open',      'x':0.5, 'y':0.45,'desc':'Empty. Manually opened from outside. Recently — frost still clings to the interior glass. Someone let them out.'},
        {'sfx':'cryo-console','type':'terminal', 'emoji':'🖥️','label':'Cryo Control Console','state':'active',    'x':0.88,'y':0.5, 'desc':'Cryogenic management system. Can initiate revival sequence, monitor occupant vitals, or emergency-vent a pod.'},
    ],
    'red_queen': [
        {'sfx':'rq-terminal',    'type':'terminal','emoji':'🖥️','label':'Red Queen Terminal',   'state':'active', 'x':0.5, 'y':0.5, 'desc':'Direct interface with the Red Queen AI. The holographic eye rotates slowly overhead. She has been aware of you since you entered.'},
        {'sfx':'override-panel', 'type':'keypad', 'emoji':'🔒','label':'AI Shutdown Override', 'state':'locked', 'x':0.15,'y':0.5, 'desc':'Emergency AI override panel. Requires three simultaneous Level 5 keycards inserted at exactly the same time. Umbrella really did not want this used.'},
        {'sfx':'research-logs',  'type':'document','emoji':'📋','label':'Classified Research Logs','state':'unsearched','x':0.88,'y':0.28,'desc':'Physical binders: T-virus origin, mutation rates, Project ALICE personnel files. This is what Umbrella is trying to bury.'},
    ],
    'executive': [
        {'sfx':'exec-terminal','type':'terminal','emoji':'🖥️','label':'Executive Terminal','state':'active',    'x':0.5,'y':0.3, 'desc':'Senior management workstation. Corporate communications, classified memos, project authorisation records.'},
        {'sfx':'safe',        'type':'locker',  'emoji':'🔒','label':'Executive Safe',    'state':'locked',    'x':0.85,'y':0.5,'desc':'Heavy floor safe. Unknown contents. Combination unknown — but the dead executive nearby may have written it down.'},
        {'sfx':'dead-exec',   'type':'body',    'emoji':'💀','label':'Dead Executive',    'state':'unsearched','x':0.5, 'y':0.7,'desc':'Senior Umbrella official. Shot once in the head — execution style. Someone cleaned up loose ends before leaving.'},
    ],
}

ACTIONS_BY_TYPE = {
    'terminal':    ['Examine', 'Use Terminal', 'Hack'],
    'locker':      ['Examine', 'Search', 'Force Open'],
    'med_cabinet': ['Examine', 'Search'],
    'drug_cabinet':['Examine', 'Pick Lock', 'Force Open'],
    'keypad':      ['Examine', 'Hack', 'Bypass'],
    'door':        ['Examine', 'Open', 'Force Open', 'Pick Lock'],
    'body':        ['Examine', 'Search Body'],
    'document':    ['Read', 'Take'],
    'electrical':  ['Examine', 'Interact'],
    'generator':   ['Examine', 'Activate'],
    'intercom':    ['Listen', 'Speak'],
    'specimen':    ['Examine'],
    'hazard':      ['Examine'],
    'cryo_pod':    ['Examine', 'Check Vitals', 'Initiate Revival'],
    'weapon_rack': ['Examine', 'Take Weapon'],
}

path = 'data/game.json'
with open(path, encoding='utf-8-sig') as f:
    d = json.load(f)

floors = d['world_map']['canvas_map']['floors']
added = 0

for fid, floor in floors.items():
    for room in floor.get('rooms', []):
        rtype = room.get('type', '')
        defs = OBJECTS_BY_TYPE.get(rtype, [])
        if not defs:
            continue
        existing_ids = {o['id'] for o in room.get('objects', [])}
        if not room.get('objects'):
            room['objects'] = []
        for od in defs:
            obj_id = f"{room['id']}-{od['sfx']}"
            if obj_id in existing_ids:
                continue
            obj = {
                'id':    obj_id,
                'type':  od['type'],
                'emoji': od['emoji'],
                'label': od['label'],
                'state': od['state'],
                'x':     od['x'],
                'y':     od['y'],
                'desc':  od['desc'],
                'actions': ACTIONS_BY_TYPE.get(od['type'], ['Examine']),
            }
            room['objects'].append(obj)
            added += 1

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print(f'Done. Added {added} objects.')
for fid, floor in floors.items():
    for room in floor.get('rooms', []):
        n = len(room.get('objects', []))
        if n:
            print(f'  {fid}/{room["id"]}: {n} objects')
