import json

path = r'C:\laragon\www\terror-infinity-rpg\system\team-gen.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    g = json.load(f)

# 1. Fix alignment attitudes to lowercase-hyphenated
fix = {
    'LOYAL': 'loyal', 'INDEPENDENT': 'independent', 'RELUCTANT': 'reluctant',
    'SELF SERVING': 'self-serving', 'AUTHORITY AVERSE': 'authority-averse',
}
for aln in g['alignments']:
    aln['attitudes'] = [fix.get(a, a.lower().replace(' ', '-')) for a in aln['attitudes']]

# 2. Add cities
cities = {
  'German':    ['Berlin','Munich','Hamburg','Cologne','Frankfurt','Stuttgart','Dusseldorf','Dresden'],
  'French':    ['Paris','Marseille','Lyon','Toulouse','Nice','Nantes','Bordeaux','Strasbourg'],
  'Italian':   ['Rome','Milan','Naples','Turin','Florence','Bologna','Venice','Palermo'],
  'Spanish':   ['Madrid','Barcelona','Valencia','Seville','Zaragoza','Malaga','Bilbao','Alicante'],
  'Polish':    ['Warsaw','Krakow','Lodz','Wroclaw','Poznan','Gdansk','Szczecin','Lublin'],
  'Russian':   ['Moscow','Saint Petersburg','Novosibirsk','Yekaterinburg','Kazan','Samara','Omsk','Volgograd'],
  'British':   ['London','Manchester','Birmingham','Glasgow','Leeds','Liverpool','Edinburgh','Bristol'],
  'Irish':     ['Dublin','Cork','Limerick','Galway','Waterford','Kilkenny','Drogheda','Sligo'],
  'Swedish':   ['Stockholm','Gothenburg','Malmo','Uppsala','Vasteras','Orebro','Linkoping','Helsingborg'],
  'Norwegian': ['Oslo','Bergen','Trondheim','Stavanger','Drammen','Fredrikstad','Tromso','Kristiansand'],
  'Dutch':     ['Amsterdam','Rotterdam','The Hague','Utrecht','Eindhoven','Tilburg','Groningen','Almere'],
  'Portuguese':['Lisbon','Porto','Braga','Coimbra','Funchal','Setubal','Evora','Faro'],
  'Ukrainian': ['Kyiv','Kharkiv','Odessa','Dnipro','Zaporizhzhia','Lviv','Kryvyi Rih','Mykolaiv'],
  'Japanese':  ['Tokyo','Osaka','Nagoya','Sapporo','Fukuoka','Kobe','Kyoto','Sendai'],
  'Korean':    ['Seoul','Busan','Incheon','Daegu','Daejeon','Gwangju','Suwon','Ulsan'],
  'Brazilian': ['Sao Paulo','Rio de Janeiro','Brasilia','Salvador','Fortaleza','Belo Horizonte','Manaus','Curitiba'],
  'Czech':     ['Prague','Brno','Ostrava','Plzen','Liberec','Olomouc','Usti nad Labem','Ceske Budejovice'],
}
for nat in g['nationalities']:
    c = nat['country']
    if c in cities:
        nat['cities'] = cities[c]

# 3. Add more occupations
new_occs = [
  {'id':'firefighter',   'label':'Firefighter',           'archetype':'combat',       'str':[13,17],'agi':[11,15],'end':[14,18],'int':[10,14],'lck':[9,13], 'psy':[10,14],'skills':['firstaid','survival','climbing']},
  {'id':'psychologist',  'label':'Psychologist',          'archetype':'academic',     'str':[6,10], 'agi':[8,12], 'end':[8,12], 'int':[14,18],'lck':[10,14],'psy':[15,19],'skills':['persuasion','perception','medicine']},
  {'id':'clergy',        'label':'Priest / Clergy',       'archetype':'academic',     'str':[6,10], 'agi':[7,11], 'end':[8,12], 'int':[12,16],'lck':[11,15],'psy':[15,19],'skills':['persuasion','medicine']},
  {'id':'farmer',        'label':'Farmer',                'archetype':'working',      'str':[12,16],'agi':[9,13], 'end':[13,17],'int':[9,13], 'lck':[11,15],'psy':[8,12], 'skills':['survival','navigation','driving']},
  {'id':'construction',  'label':'Construction Worker',   'archetype':'working',      'str':[14,18],'agi':[10,14],'end':[13,17],'int':[8,12], 'lck':[9,13], 'psy':[6,10], 'skills':['engineering','climbing','melee']},
  {'id':'pilot_civ',     'label':'Civilian Pilot',        'archetype':'technical',    'str':[9,13], 'agi':[12,16],'end':[10,14],'int':[14,18],'lck':[12,16],'psy':[11,15],'skills':['navigation','engineering','perception']},
  {'id':'vet',           'label':'Veterinarian',          'archetype':'medical',      'str':[9,13], 'agi':[10,14],'end':[9,13], 'int':[14,18],'lck':[9,13], 'psy':[12,16],'skills':['medicine','firstaid','biology']},
  {'id':'diver',         'label':'Professional Diver',    'archetype':'athletic',     'str':[11,15],'agi':[13,17],'end':[13,17],'int':[10,14],'lck':[10,14],'psy':[9,13], 'skills':['diving','survival','perception']},
  {'id':'mercenary',     'label':'Mercenary',             'archetype':'combat',       'str':[13,17],'agi':[12,16],'end':[13,17],'int':[10,14],'lck':[10,14],'psy':[7,11], 'skills':['firearms','tactics','melee','survival']},
  {'id':'forensic',      'label':'Forensic Specialist',   'archetype':'investigative','str':[7,11], 'agi':[9,13], 'end':[8,12], 'int':[15,19],'lck':[11,15],'psy':[12,16],'skills':['perception','chemistry','medicine']},
  {'id':'trainer',       'label':'Personal Trainer',      'archetype':'athletic',     'str':[12,16],'agi':[13,17],'end':[13,17],'int':[9,13], 'lck':[9,13], 'psy':[10,14],'skills':['agility_training','endurance_training','medicine']},
  {'id':'hunter',        'label':'Hunter / Outdoorsman',  'archetype':'athletic',     'str':[12,16],'agi':[13,17],'end':[13,17],'int':[10,14],'lck':[12,16],'psy':[8,12], 'skills':['survival','navigation','firearms','perception']},
  {'id':'scientist',     'label':'Research Scientist',    'archetype':'academic',     'str':[6,10], 'agi':[8,12], 'end':[7,11], 'int':[16,20],'lck':[9,13], 'psy':[11,15],'skills':['chemistry','biology','engineering']},
  {'id':'sailor',        'label':'Sailor',                'archetype':'working',      'str':[11,15],'agi':[11,15],'end':[12,16],'int':[10,14],'lck':[11,15],'psy':[8,12], 'skills':['navigation','survival','diving','melee']},
  {'id':'stuntman',      'label':'Stunt Performer',       'archetype':'athletic',     'str':[11,15],'agi':[15,19],'end':[12,16],'int':[9,13], 'lck':[13,17],'psy':[9,13], 'skills':['agility_training','climbing','driving']},
  {'id':'bodyguard',     'label':'Bodyguard',             'archetype':'combat',       'str':[13,17],'agi':[12,16],'end':[13,17],'int':[11,15],'lck':[10,14],'psy':[9,13], 'skills':['firearms','melee','perception','tactics']},
  {'id':'archaeologist', 'label':'Archaeologist',         'archetype':'academic',     'str':[9,13], 'agi':[10,14],'end':[10,14],'int':[14,18],'lck':[11,15],'psy':[10,14],'skills':['perception','survival','navigation']},
  {'id':'social_worker', 'label':'Social Worker',         'archetype':'academic',     'str':[7,11], 'agi':[9,13], 'end':[9,13], 'int':[12,16],'lck':[10,14],'psy':[14,18],'skills':['persuasion','perception']},
]
existing_ids = {o['id'] for o in g['occupations']}
for o in new_occs:
    if o['id'] not in existing_ids:
        g['occupations'].append(o)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(g, f, ensure_ascii=False, indent=2)
print('Done. Occupations:', len(g['occupations']), '| Nationalities:', len(g['nationalities']))
print('Sample attitudes:', g['alignments'][1]['attitudes'])
print('Sample cities (German):', g['nationalities'][0].get('cities', 'MISSING'))
