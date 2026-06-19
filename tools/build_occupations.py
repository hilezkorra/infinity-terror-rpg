#!/usr/bin/env python3
"""
Expand team-gen.json occupations with rarity tiers + 160 occupations.
Replaces the flat occupations array with a rarity-gated system.

Usage: python tools/build_occupations.py
"""

import json, copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEAM_GEN = ROOT / 'system' / 'team-gen.json'

# ── helpers ────────────────────────────────────────────────────
def occ(id_, label, archetype, rarity, tags, str_r, agi_r, end_r, int_r, lck_r, psy_r, skills):
    return {
        'id': id_, 'label': label, 'archetype': archetype,
        'rarity': rarity, 'tags': tags,
        'str': str_r, 'agi': agi_r, 'end': end_r,
        'int': int_r, 'lck': lck_r, 'psy': psy_r,
        'skills': skills
    }

# ════════════════════════════════════════════════════════════════
# RARITY: common(40%) / uncommon(30%) / rare(16%) / very_rare(10%) / legendary(4%)
# ════════════════════════════════════════════════════════════════

NEW = []

# ── COMMON (≈60) — everyday jobs, no special training needed ──
C = 'common'

NEW.append(occ('office_worker','Office Worker','working',C,['civilian'],
    [7,11],[8,12],[8,12],[11,15],[9,13],[10,14],['typing','organization','computer_basic']))
NEW.append(occ('retail_associate','Retail Sales Associate','working',C,['civilian'],
    [8,12],[9,13],[9,13],[9,13],[10,14],[8,12],['customer_service','cash_handling']))
NEW.append(occ('cashier','Cashier','working',C,['civilian'],
    [7,11],[9,13],[9,13],[8,12],[10,14],[8,12],['cash_handling','customer_service']))
NEW.append(occ('waiter','Waiter/Waitress','working',C,['civilian'],
    [8,12],[11,15],[10,14],[9,13],[10,14],[10,14],['customer_service','multi_tasking']))
NEW.append(occ('bartender','Bartender','working',C,['civilian'],
    [9,13],[11,15],[10,14],[10,14],[10,14],[12,16],['customer_service','multi_tasking']))
NEW.append(occ('barista','Barista','working',C,['civilian'],
    [7,11],[10,14],[9,13],[9,13],[9,13],[10,14],['customer_service','multi_tasking']))
NEW.append(occ('cook_line','Line Cook','working',C,['civilian'],
    [11,15],[11,15],[12,16],[8,12],[8,12],[8,12],['knife_combat','multi_tasking']))
NEW.append(occ('cleaner','Cleaner/Janitor','working',C,['civilian'],
    [10,14],[9,13],[11,15],[7,11],[9,13],[7,11],['cleaning_industrial','basic_repair']))
NEW.append(occ('warehouse','Warehouse Worker','working',C,['civilian'],
    [12,16],[9,13],[12,16],[7,11],[9,13],[6,10],['lifting','forklift_basic']))
NEW.append(occ('delivery_driver','Delivery Driver','working',C,['civilian'],
    [9,13],[10,14],[10,14],[8,12],[11,15],[8,12],['driving','navigation']))
NEW.append(occ('security_guard','Security Guard','working',C,['civilian'],
    [11,15],[9,13],[11,15],[8,12],[9,13],[8,12],['observation','basic_firstaid']))
NEW.append(occ('construction_labor','Construction Laborer','working',C,['civilian'],
    [14,18],[10,14],[14,18],[7,11],[8,12],[6,10],['lifting','tool_use_basic']))
NEW.append(occ('factory_worker','Factory Worker','working',C,['civilian'],
    [11,15],[8,12],[12,16],[7,11],[8,12],[6,10],['machine_operation','quality_check']))
NEW.append(occ('farm_worker','Farm Worker','working',C,['civilian'],
    [13,17],[10,14],[14,18],[8,12],[10,14],[7,11],['animal_handling','driving','crop_knowledge']))
NEW.append(occ('fisherman','Fisherman','working',C,['civilian','maritime'],
    [12,16],[11,15],[13,17],[9,13],[11,15],[8,12],['swimming','navigation','fish_cleaning']))
NEW.append(occ('gardener','Gardener/Landscaper','working',C,['civilian'],
    [12,16],[10,14],[12,16],[9,13],[9,13],[8,12],['plant_identification','tool_use_basic']))
NEW.append(occ('housekeeper','Housekeeper','working',C,['civilian'],
    [9,13],[10,14],[10,14],[8,12],[9,13],[8,12],['cleaning','organization']))
NEW.append(occ('nanny','Nanny/Childcare','working',C,['civilian'],
    [8,12],[10,14],[9,13],[10,14],[10,14],[13,17],['childcare','basic_firstaid','cooking']))
NEW.append(occ('receptionist','Receptionist','working',C,['civilian'],
    [7,11],[9,13],[8,12],[10,14],[10,14],[12,16],['customer_service','phone_etiquette','organization']))
NEW.append(occ('call_center','Call Center Agent','working',C,['civilian'],
    [6,10],[8,12],[8,12],[10,14],[9,13],[11,15],['customer_service','typing','complaint_handling']))
NEW.append(occ('stock_clerk','Shelf Stocker','working',C,['civilian'],
    [11,15],[9,13],[11,15],[7,11],[9,13],[7,11],['lifting','organization','inventory']))
NEW.append(occ('parking_attendant','Parking Attendant','working',C,['civilian'],
    [9,13],[9,13],[10,14],[8,12],[10,14],[8,12],['customer_service','basic_math']))
NEW.append(occ('laundry_worker','Laundry Worker','working',C,['civilian'],
    [10,14],[8,12],[11,15],[7,11],[8,12],[6,10],['fabric_care','stain_treatment']))
NEW.append(occ('dishwasher','Dishwasher','working',C,['civilian'],
    [10,14],[9,13],[12,16],[6,10],[8,12],[6,10],['cleaning_industrial','machine_operation']))
NEW.append(occ('fast_food','Fast Food Worker','working',C,['civilian'],
    [9,13],[10,14],[10,14],[8,12],[9,13],[8,12],['customer_service','cash_handling','multi_tasking']))
NEW.append(occ('newspaper_delivery','Newspaper Deliverer','working',C,['civilian'],
    [8,12],[10,14],[9,13],[7,11],[10,14],[7,11],['driving_basic','navigation','early_rising']))
NEW.append(occ('trash_collector','Trash Collector','working',C,['civilian'],
    [14,18],[8,12],[14,18],[6,10],[8,12],[6,10],['lifting','route_memory']))
NEW.append(occ('painter','Painter (decorative)','working',C,['civilian'],
    [11,15],[11,15],[11,15],[8,12],[9,13],[8,12],['painting','surface_prep','tool_use_basic']))
NEW.append(occ('postman','Postman/Mail Carrier','working',C,['civilian'],
    [10,14],[10,14],[12,16],[9,13],[10,14],[8,12],['navigation','route_memory','organization']))
NEW.append(occ('cab_driver','Cab Driver','working',C,['civilian'],
    [8,12],[9,13],[9,13],[9,13],[11,15],[9,13],['driving','navigation','customer_service']))
NEW.append(occ('bus_driver','Bus Driver','working',C,['civilian'],
    [9,13],[10,14],[11,15],[10,14],[10,14],[9,13],['driving_heavy','navigation','customer_service']))
NEW.append(occ('bakery_assistant','Bakery Assistant','working',C,['civilian'],
    [10,14],[9,13],[10,14],[8,12],[9,13],[8,12],['baking_basic','customer_service','cleaning']))
NEW.append(occ('butcher_shop','Butcher Shop Worker','working',C,['civilian'],
    [12,16],[10,14],[11,15],[8,12],[9,13],[8,12],['butchering','knife_combat','customer_service']))
NEW.append(occ('fishmonger','Fishmonger','working',C,['civilian','maritime'],
    [11,15],[9,13],[11,15],[8,12],[10,14],[8,12],['fish_cleaning','customer_service','cold_storage']))
NEW.append(occ('greengrocer','Greengrocer','working',C,['civilian'],
    [10,14],[9,13],[10,14],[9,13],[10,14],[9,13],['produce_knowledge','customer_service','inventory']))
NEW.append(occ('lifeguard','Lifeguard','working',C,['civilian','safety'],
    [11,15],[14,18],[13,17],[10,14],[11,15],[10,14],['swimming','firstaid','rescue_techniques','observation']))
NEW.append(occ('toll_operator','Toll Booth Operator','working',C,['civilian'],
    [7,11],[8,12],[8,12],[8,12],[9,13],[8,12],['cash_handling','customer_service']))
NEW.append(occ('moving_crew','Moving Crew Worker','working',C,['civilian'],
    [14,18],[9,13],[13,17],[7,11],[8,12],[6,10],['lifting','packing','driving_basic']))
NEW.append(occ('courier','Courier/Messenger','working',C,['civilian'],
    [9,13],[12,16],[10,14],[9,13],[12,16],[8,12],['navigation','driving_basic','speed_running','route_optimization']))
NEW.append(occ('food_truck','Food Truck Operator','working',C,['civilian'],
    [10,14],[9,13],[11,15],[10,14],[10,14],[10,14],['cooking','driving','customer_service','cash_handling']))
NEW.append(occ('pet_groomer','Pet Groomer','working',C,['civilian'],
    [9,13],[11,15],[10,14],[9,13],[9,13],[10,14],['animal_handling','grooming','customer_service']))
NEW.append(occ('dry_cleaner','Dry Cleaner Attendant','working',C,['civilian'],
    [9,13],[8,12],[10,14],[8,12],[9,13],[8,12],['fabric_care','chemical_handling','customer_service']))
NEW.append(occ('car_wash','Car Wash Attendant','working',C,['civilian'],
    [10,14],[9,13],[11,15],[7,11],[9,13],[7,11],['cleaning','basic_maintenance','customer_service']))
NEW.append(occ('valet','Valet Parking Attendant','working',C,['civilian'],
    [9,13],[11,15],[10,14],[8,12],[11,15],[9,13],['driving','customer_service','running']))
NEW.append(occ('dishwasher','Dishwasher','working',C,['civilian'],
    [11,15],[8,12],[12,16],[6,10],[8,12],[6,10],['cleaning_industrial','machine_operation']))
NEW.append(occ('stagehand','Stagehand','working',C,['civilian','entertainment'],
    [12,16],[11,15],[12,16],[9,13],[9,13],[8,12],['lifting','rigging_basic','tool_use_basic','lighting_basic']))
NEW.append(occ('usher','Usher/Theater Attendant','working',C,['civilian','entertainment'],
    [7,11],[9,13],[9,13],[9,13],[9,13],[11,15],['customer_service','crowd_control','orientation']))
NEW.append(occ('park_ranger','Park Ranger (junior)','working',C,['civilian','outdoor'],
    [11,15],[11,15],[12,16],[10,14],[10,14],[10,14],['navigation','firstaid','wildlife_knowledge','survival_basic']))

# ── UNCOMMON (≈50) — skilled trades, trained specialists ──────
U = 'uncommon'

NEW.append(occ('nurse_licensed','Registered Nurse','medical',U,['medical'],
    [9,13],[11,15],[11,15],[14,18],[10,14],[13,17],['medicine','firstaid','patient_care','diagnosis_basic']))
NEW.append(occ('electrician','Electrician','technical',U,['skilled_trade'],
    [11,15],[11,15],[11,15],[13,17],[9,13],[8,12],['electrical_wiring','blueprint_reading','safety_protocol','troubleshooting']))
NEW.append(occ('plumber','Plumber','technical',U,['skilled_trade'],
    [12,16],[10,14],[11,15],[12,16],[9,13],[8,12],['plumbing','pipe_fitting','blueprint_reading','troubleshooting']))
NEW.append(occ('carpenter','Carpenter','technical',U,['skilled_trade'],
    [13,17],[11,15],[12,16],[11,15],[9,13],[8,12],['carpentry','blueprint_reading','tool_use','measuring']))
NEW.append(occ('mechanic_auto','Auto Mechanic','technical',U,['skilled_trade'],
    [12,16],[10,14],[12,16],[12,16],[9,13],[8,12],['mechanical_repair','diagnostics','welding_basic','tool_use']))
NEW.append(occ('hairdresser','Hairdresser/Stylist','working',U,['beauty'],
    [8,12],[11,15],[9,13],[10,14],[10,14],[13,17],['hair_styling','customer_service','creativity','color_theory']))
NEW.append(occ('beautician','Beautician/Cosmetologist','working',U,['beauty'],
    [7,11],[10,14],[9,13],[10,14],[10,14],[13,17],['skincare','makeup','customer_service','product_knowledge']))
NEW.append(occ('tailor','Tailor/Seamstress','technical',U,['skilled_trade'],
    [8,12],[13,17],[10,14],[11,15],[10,14],[9,13],['sewing','pattern_making','fabric_knowledge','measuring']))
NEW.append(occ('photographer','Photographer','creative',U,['creative'],
    [7,11],[10,14],[9,13],[12,16],[11,15],[11,15],['photography','editing','composition','lighting']))
NEW.append(occ('graphic_designer','Graphic Designer','creative',U,['creative','technical'],
    [6,10],[9,13],[8,12],[13,17],[10,14],[11,15],['design_software','typography','layout','branding']))
NEW.append(occ('real_estate','Real Estate Agent','working',U,['business'],
    [7,11],[9,13],[9,13],[12,16],[14,18],[13,17],['negotiation','sales','market_knowledge','persuasion']))
NEW.append(occ('fitness_trainer','Fitness Trainer','athletic',U,['fitness'],
    [12,16],[12,16],[12,16],[10,14],[9,13],[11,15],['exercise_programming','anatomy_basic','nutrition_basic','motivation']))
NEW.append(occ('yoga_instructor','Yoga Instructor','athletic',U,['fitness'],
    [9,13],[14,18],[12,16],[11,15],[10,14],[14,18],['yoga','meditation','flexibility','breath_control']))
NEW.append(occ('martial_arts_instructor','Martial Arts Instructor','combat',U,['martial'],
    [12,16],[13,17],[12,16],[11,15],[10,14],[13,17],['martial_arts','teaching','discipline','body_control']))
NEW.append(occ('paramedic','Paramedic','medical',U,['medical','emergency'],
    [10,14],[12,16],[11,15],[14,18],[11,15],[12,16],['firstaid','emergency_response','driving','triage']))
NEW.append(occ('firefighter','Firefighter','combat',U,['emergency','safety'],
    [14,18],[12,16],[15,19],[11,15],[10,14],[11,15],['rescue','firstaid','climbing','survival','equipment_operation']))
NEW.append(occ('police_officer','Police Officer','combat',U,['law_enforcement'],
    [12,16],[11,15],[12,16],[12,16],[11,15],[11,15],['firearms','melee','perception','law_knowledge','driving']))
NEW.append(occ('soldier_enlisted','Soldier (Enlisted)','combat',U,['military'],
    [13,17],[12,16],[13,17],[10,14],[9,13],[9,13],['firearms','melee','survival','drill','team_tactics']))
NEW.append(occ('dental_assistant','Dental Assistant','medical',U,['medical'],
    [8,12],[10,14],[9,13],[12,16],[10,14],[11,15],['patient_care','sterilization','instrument_handling','xray_basic']))
NEW.append(occ('vet_tech','Veterinary Technician','medical',U,['medical','animal'],
    [9,13],[10,14],[10,14],[13,17],[9,13],[12,16],['animal_care','medicine','surgery_assist','lab_work']))
NEW.append(occ('pharmacy_tech','Pharmacy Technician','medical',U,['medical'],
    [7,11],[9,13],[9,13],[13,17],[10,14],[11,15],['pharmacology','medication_knowledge','customer_service','precision']))
NEW.append(occ('it_technician','IT Technician','technical',U,['technical'],
    [7,11],[10,14],[8,12],[14,18],[10,14],[9,13],['computer_repair','networking','troubleshooting','customer_service']))
NEW.append(occ('web_developer','Web Developer','technical',U,['technical','creative'],
    [6,10],[9,13],[8,12],[15,19],[11,15],[10,14],['programming','web_design','problem_solving','database']))
NEW.append(occ('social_media_mgr','Social Media Manager','creative',U,['creative','business'],
    [6,10],[9,13],[8,12],[12,16],[12,16],[12,16],['social_media','content_creation','analytics','trend_awareness']))
NEW.append(occ('accountant','Accountant','working',U,['business','finance'],
    [6,10],[8,12],[9,13],[14,18],[10,14],[9,13],['accounting','tax_knowledge','spreadsheets','auditing']))
NEW.append(occ('bookkeeper','Bookkeeper','working',U,['business','finance'],
    [7,11],[9,13],[9,13],[12,16],[10,14],[9,13],['bookkeeping','spreadsheets','organization','attention_to_detail']))
NEW.append(occ('insurance_agent','Insurance Agent','working',U,['business','sales'],
    [7,11],[9,13],[9,13],[12,16],[12,16],[13,17],['sales','negotiation','policy_knowledge','customer_service']))
NEW.append(occ('travel_agent','Travel Agent','working',U,['business','hospitality'],
    [6,10],[9,13],[8,12],[12,16],[11,15],[13,17],['booking_systems','destination_knowledge','customer_service','planning']))
NEW.append(occ('event_coordinator','Event Coordinator','working',U,['business','creative'],
    [8,12],[10,14],[10,14],[12,16],[11,15],[13,17],['planning','negotiation','multitasking','vendor_management']))
NEW.append(occ('interior_designer','Interior Designer','creative',U,['creative'],
    [7,11],[9,13],[8,12],[12,16],[11,15],[12,16],['design','space_planning','color_theory','vendor_knowledge']))
NEW.append(occ('florist','Florist','working',U,['creative'],
    [8,12],[10,14],[9,13],[10,14],[10,14],[11,15],['floral_arrangement','plant_knowledge','customer_service','creativity']))
NEW.append(occ('jeweler','Jeweler','technical',U,['skilled_trade','craft'],
    [8,12],[13,17],[10,14],[12,16],[10,14],[10,14],['jewelry_making','precision_work','gemology','repair']))
NEW.append(occ('watchmaker','Watchmaker','technical',U,['skilled_trade','craft'],
    [7,11],[14,18],[10,14],[14,18],[10,14],[9,13],['precision_assembly','micro_mechanics','repair','patience']))
NEW.append(occ('locksmith','Locksmith','technical',U,['skilled_trade','security'],
    [10,14],[12,16],[10,14],[12,16],[11,15],[9,13],['lockpicking','key_making','safe_basic','security_knowledge']))
NEW.append(occ('chef_executive','Chef (Executive)','working',U,['culinary'],
    [11,15],[12,16],[12,16],[13,17],[10,14],[11,15],['cooking','kitchen_management','menu_planning','knife_combat']))
NEW.append(occ('restaurant_manager','Restaurant Manager','working',U,['business','hospitality'],
    [9,13],[10,14],[11,15],[13,17],[11,15],[13,17],['management','customer_service','inventory','staff_training']))
NEW.append(occ('flight_attendant','Flight Attendant','working',U,['aviation','hospitality'],
    [8,12],[10,14],[9,13],[11,15],[12,16],[14,18],['safety_protocol','firstaid','customer_service','crisis_management']))
NEW.append(occ('train_conductor','Train Conductor','working',U,['transport'],
    [9,13],[9,13],[11,15],[12,16],[10,14],[9,13],['equipment_operation','safety_protocol','navigation','scheduling']))
NEW.append(occ('truck_driver_long','Truck Driver (Long Haul)','working',U,['transport'],
    [11,15],[9,13],[12,16],[9,13],[11,15],[8,12],['driving_heavy','navigation','endurance','basic_mechanics']))
NEW.append(occ('private_investigator','Private Investigator','investigative',U,['investigation'],
    [9,13],[11,15],[10,14],[13,17],[13,17],[12,16],['perception','surveillance','research','lockpicking']))
NEW.append(occ('baker_master','Master Baker','working',U,['culinary'],
    [11,15],[10,14],[11,15],[12,16],[10,14],[10,14],['baking','dough_preparation','recipe_creation','time_management']))
NEW.append(occ('sous_chef','Sous Chef','working',U,['culinary'],
    [12,16],[12,16],[13,17],[11,15],[9,13],[10,14],['cooking_advanced','team_leadership','knife_combat','plating']))
NEW.append(occ('winemaker','Winemaker','working',U,['culinary','craft'],
    [10,14],[10,14],[11,15],[13,17],[11,15],[10,14],['wine_knowledge','fermentation','tasting','chemistry_basic']))
NEW.append(occ('brewer','Brewer','working',U,['culinary','craft'],
    [10,14],[9,13],[11,15],[12,16],[10,14],[9,13],['brewing','fermentation','chemistry_basic','quality_control']))
NEW.append(occ('fishing_captain','Fishing Boat Captain','working',U,['maritime'],
    [12,16],[11,15],[13,17],[11,15],[12,16],[9,13],['navigation','fishing','vessel_operation','weather_reading','leadership']))
NEW.append(occ('construction_framer','Construction Framer','working',U,['skilled_trade'],
    [14,18],[11,15],[13,17],[10,14],[8,12],[7,11],['carpentry','blueprint_reading','tool_use','teamwork']))
NEW.append(occ('heavy_equip_op','Heavy Equipment Operator','working',U,['skilled_trade'],
    [12,16],[10,14],[12,16],[11,15],[9,13],[8,12],['equipment_operation','safety_protocol','site_awareness','basic_mechanics']))
NEW.append(occ('surveyor','Surveyor','technical',U,['technical','outdoor'],
    [10,14],[11,15],[12,16],[14,18],[10,14],[8,12],['surveying','math_advanced','map_reading','equipment_operation']))

# ── RARE (≈25) — requires education, rare talent, opportunity ─
R = 'rare'

NEW.append(occ('doctor_gp','General Practitioner','medical',R,['medical','professional'],
    [8,12],[10,14],[10,14],[16,20],[10,14],[13,17],['medicine','diagnosis','patient_care','pharmacology','anatomy']))
NEW.append(occ('surgeon','Surgeon','medical',R,['medical','professional'],
    [9,13],[14,18],[11,15],[17,21],[10,14],[12,16],['surgery','anatomy','precision','diagnosis','crisis_management']))
NEW.append(occ('lawyer','Lawyer','working',R,['professional','legal'],
    [7,11],[9,13],[9,13],[16,20],[12,16],[14,18],['legal_knowledge','negotiation','argumentation','research','persuasion']))
NEW.append(occ('judge','Judge','working',R,['professional','legal'],
    [6,10],[8,12],[9,13],[16,20],[13,17],[15,19],['legal_knowledge','judgment','authority','psychology','public_speaking']))
NEW.append(occ('engineer','Engineer (Civil/Mechanical/Electrical)','technical',R,['professional','technical'],
    [9,13],[10,14],[10,14],[16,20],[10,14],[9,13],['engineering','math_advanced','problem_solving','design','project_management']))
NEW.append(occ('software_engineer','Software Engineer','technical',R,['professional','technical'],
    [7,11],[10,14],[8,12],[17,21],[11,15],[10,14],['programming','algorithms','system_design','problem_solving','team_collaboration']))
NEW.append(occ('data_scientist','Data Scientist','technical',R,['professional','technical'],
    [6,10],[9,13],[8,12],[17,21],[11,15],[10,14],['statistics','programming','machine_learning','analytics','domain_knowledge']))
NEW.append(occ('architect','Architect','technical',R,['professional','creative'],
    [9,13],[10,14],[9,13],[16,20],[10,14],[11,15],['design','engineering','blueprint_reading','spatial_awareness','project_management']))
NEW.append(occ('university_prof','University Professor','academic',R,['professional','academic'],
    [6,10],[8,12],[8,12],[17,21],[10,14],[13,17],['teaching','research','public_speaking','writing','domain_expertise']))
NEW.append(occ('research_scientist','Research Scientist','academic',R,['professional','academic'],
    [7,11],[9,13],[8,12],[17,21],[10,14],[11,15],['research','experiment_design','data_analysis','domain_expertise','writing']))
NEW.append(occ('chemist','Chemist','academic',R,['professional','academic'],
    [8,12],[10,14],[9,13],[16,20],[9,13],[10,14],['chemistry','lab_technique','analysis','compound_synthesis','safety']))
NEW.append(occ('pharmacologist','Pharmacologist','medical',R,['medical','professional'],
    [7,11],[10,14],[9,13],[16,20],[10,14],[11,15],['pharmacology','medicine','chemistry','research','drug_development']))
NEW.append(occ('psychiatrist','Psychiatrist','medical',R,['medical','professional'],
    [6,10],[8,12],[8,12],[16,20],[11,15],[16,20],['psychiatry','psychology','diagnosis','medication','therapy']))
NEW.append(occ('veterinarian','Veterinarian','medical',R,['medical','professional','animal'],
    [9,13],[10,14],[10,14],[16,20],[10,14],[13,17],['veterinary_medicine','surgery','diagnosis','animal_handling','pharmacology']))
NEW.append(occ('detective_homicide','Homicide Detective','investigative',R,['law_enforcement','investigation'],
    [10,14],[11,15],[11,15],[15,19],[13,17],[13,17],['investigation','interrogation','crime_scene','perception','firearms']))
NEW.append(occ('journalist_investigative','Investigative Journalist','academic',R,['media','investigation'],
    [7,11],[10,14],[9,13],[14,18],[13,17],[13,17],['investigation','writing','interviewing','source_handling','research']))
NEW.append(occ('novelist','Novelist','creative',R,['creative','professional'],
    [6,10],[8,12],[8,12],[15,19],[12,16],[14,18],['writing','storytelling','research','creativity','discipline']))
NEW.append(occ('film_director','Film Director','creative',R,['creative','professional'],
    [8,12],[10,14],[11,15],[15,19],[12,16],[14,18],['directing','storytelling','leadership','creative_vision','communication']))
NEW.append(occ('professional_musician','Professional Musician','creative',R,['creative','professional'],
    [8,12],[14,18],[11,15],[13,17],[12,16],[14,18],['instrument_mastery','music_theory','performance','composition','practice']))
NEW.append(occ('professional_athlete','Professional Athlete','athletic',R,['athletic','professional'],
    [15,19],[15,19],[15,19],[10,14],[12,16],[10,14],['athletic_specialty','training','competition','discipline','nutrition']))
NEW.append(occ('commercial_pilot','Commercial Airline Pilot','technical',R,['aviation','professional'],
    [9,13],[13,17],[11,15],[15,19],[13,17],[12,16],['flying','navigation','engineering','crisis_management','communication']))
NEW.append(occ('ship_captain','Ship Captain','working',R,['maritime','professional'],
    [12,16],[11,15],[13,17],[14,18],[13,17],[12,16],['navigation','vessel_operation','leadership','weather_reading','crisis_management']))
NEW.append(occ('diplomat','Diplomat','working',R,['government','professional'],
    [7,11],[9,13],[9,13],[15,19],[13,17],[16,20],['negotiation','persuasion','cultural_knowledge','protocol','language_skills']))
NEW.append(occ('intelligence_analyst','Intelligence Analyst','investigative',R,['government','investigation'],
    [8,12],[10,14],[9,13],[16,20],[12,16],[12,16],['analysis','research','pattern_recognition','security_knowledge','report_writing']))
NEW.append(occ('special_forces','Special Forces Operator','combat',R,['military','combat'],
    [16,20],[15,19],[16,20],[13,17],[11,15],[12,16],['firearms_master','tactics','survival','demolitions','melee_master']))

# ── VERY RARE (≈15) — exceptional, niche, high-level ──────────
VR = 'very_rare'

NEW.append(occ('ceo','Corporate CEO','working',VR,['business','elite'],
    [8,12],[9,13],[11,15],[16,20],[15,19],[15,19],['leadership','strategy','negotiation','finance','crisis_management']))
NEW.append(occ('fighter_pilot','Fighter Jet Pilot','combat',VR,['military','aviation'],
    [11,15],[15,19],[12,16],[16,20],[15,19],[13,17],['flying_combat','navigation','tactical_thinking','g_tolerance','crisis_management']))
NEW.append(occ('spy_field','Field Intelligence Operative','investigative',VR,['government','espionage'],
    [10,14],[14,18],[11,15],[16,20],[14,18],[14,18],['espionage','tradecraft','interrogation','surveillance','firearms','disguise']))
NEW.append(occ('deep_cover_op','Deep Cover Operative','investigative',VR,['government','espionage','criminal'],
    [11,15],[13,17],[12,16],[15,19],[15,19],[14,18],['espionage','improv','deception','survival','firearms','language_mastery']))
NEW.append(occ('hitman','Professional Hitman','combat',VR,['criminal','combat'],
    [12,16],[15,19],[12,16],[14,18],[14,18],[11,15],['firearms_master','stealth','stalking','escape_planning','melee']))
NEW.append(occ('cartel_lieutenant','Cartel Lieutenant','working',VR,['criminal','organized_crime'],
    [13,17],[12,16],[14,18],[13,17],[13,17],[13,17],['leadership','firearms','intimidation','logistics','negotiation']))
NEW.append(occ('crime_boss','Crime Boss (City)','working',VR,['criminal','organized_crime'],
    [11,15],[10,14],[12,16],[15,19],[14,18],[16,20],['leadership','intimidation','strategy','corruption','networking']))
NEW.append(occ('human_trafficker','Human Trafficker','working',VR,['criminal'],
    [10,14],[11,15],[11,15],[14,18],[14,18],[13,17],['logistics','intimidation','deception','navigation','corruption']))
NEW.append(occ('arms_dealer','Arms Dealer','working',VR,['criminal','military'],
    [10,14],[10,14],[11,15],[15,19],[15,19],[14,18],['weapons_knowledge','logistics','negotiation','networking','deception']))
NEW.append(occ('mercenary_leader','Mercenary Commander','combat',VR,['military','combat'],
    [15,19],[14,18],[15,19],[14,18],[13,17],[13,17],['tactics_master','leadership','firearms_master','survival','strategy']))
NEW.append(occ('black_ops_vet','Black Operations Veteran','combat',VR,['military','combat','government'],
    [15,19],[15,19],[15,19],[14,18],[13,17],[13,17],['covert_ops','tactics','demolitions','survival','interrogation']))
NEW.append(occ('astronaut','Astronaut','technical',VR,['science','exploration'],
    [10,14],[12,16],[13,17],[17,21],[14,18],[14,18],['engineering','survival','pilot','science','teamwork','crisis_management']))
NEW.append(occ('olympian','Olympic Medalist','athletic',VR,['athletic','elite'],
    [16,20],[17,21],[16,20],[11,15],[14,18],[12,16],['athletic_specialty','peak_condition','competition','discipline','coaching']))
NEW.append(occ('world_champ_fighter','World Champion Fighter','combat',VR,['combat','martial'],
    [17,21],[16,20],[17,21],[11,15],[13,17],[13,17],['martial_master','fight_iq','endurance','strike_precision','combat_sense']))
NEW.append(occ('cyber_criminal','Elite Cyber Criminal','technical',VR,['criminal','technical'],
    [7,11],[11,15],[9,13],[18,22],[14,18],[10,14],['hacking','social_engineering','network_penetration','cryptography','anonymity']))
NEW.append(occ('cult_leader','Cult Leader','working',VR,['criminal','manipulative'],
    [8,12],[9,13],[10,14],[16,20],[15,19],[18,22],['manipulation','charisma','psychology','indoctrination','planning']))
NEW.append(occ('drug_lord','Drug Lord (Regional)','working',VR,['criminal','organized_crime'],
    [12,16],[11,15],[13,17],[14,18],[15,19],[15,19],['leadership','intimidation','logistics','corruption','firearms','strategy']))

# ── LEGENDARY (≈10) — one in a million ─────────────────────────
L = 'legendary'

NEW.append(occ('president','Country President/Prime Minister','working',L,['government','elite','power'],
    [8,12],[9,13],[11,15],[17,21],[16,20],[18,22],['leadership','strategy','public_speaking','negotiation','crisis_management','political_acumen']))
NEW.append(occ('terrorist_leader','Terrorist Organization Leader','combat',L,['criminal','combat','power'],
    [13,17],[14,18],[14,18],[17,21],[14,18],[18,22],['leadership','tactics_master','survival','explosives','deception','indoctrination']))
NEW.append(occ('mass_serial_killer','Mass Serial Killer','working',L,['criminal','killer'],
    [12,16],[13,17],[12,16],[15,19],[14,18],[15,19],['killing','stalking','deception','planning','escape','psychopathy']))
NEW.append(occ('super_soldier','Super Soldier (Experimental)','combat',L,['military','augmented','combat'],
    [19,25],[18,24],[19,25],[13,17],[12,16],[12,16],['enhanced_combat','enhanced_reflexes','enhanced_endurance','tactics','firearms_master','survival']))
NEW.append(occ('syndicate_leader','International Crime Syndicate Leader','working',L,['criminal','organized_crime','power'],
    [11,15],[11,15],[12,16],[18,22],[17,21],[18,22],['leadership','strategy_master','corruption','networking','finance','intimidation']))
NEW.append(occ('cartel_supreme','Cartel Supreme Leader','working',L,['criminal','organized_crime','power'],
    [13,17],[11,15],[14,18],[16,20],[16,20],[18,22],['leadership','intimidation','strategy','logistics','corruption','brutality']))
NEW.append(occ('secret_society_gm','Secret Society Grandmaster','working',L,['power','occult'],
    [9,13],[11,15],[11,15],[18,22],[17,21],[18,22],['manipulation','hidden_knowledge','networking','deception','strategy','resources']))
NEW.append(occ('nobel_genius','World-Renowned Genius (Nobel/Fields)','academic',L,['science','genius'],
    [6,10],[9,13],[8,12],[20,25],[12,16],[13,17],['genius_intellect','discovery','research_master','problem_solving','domain_mastery']))
NEW.append(occ('warlord','Warlord','combat',L,['military','power'],
    [16,20],[13,17],[17,21],[15,19],[14,18],[15,19],['leadership','tactics_master','survival','brutality','firearms_master','strategy']))
NEW.append(occ('master_assassin','Legendary Master Assassin','combat',L,['criminal','killer','combat'],
    [13,17],[19,25],[14,18],[16,20],[16,20],[13,17],['assassination','stealth_master','combat_master','poison','disguise','escape_master']))
NEW.append(occ('dictator','Dictator','working',L,['government','power'],
    [10,14],[9,13],[12,16],[17,21],[15,19],[19,25],['leadership','intimidation','political_acumen','strategy','brutality','propaganda']))

# ════════════════════════════════════════════════════════════════
# MISSING ARCHETYPES FROM OLD LIST — add critical ones
# ════════════════════════════════════════════════════════════════

# Uncommon additions — important archetypes the old list had
U = 'uncommon'

NEW.append(occ('parkour_practitioner','Parkour Practitioner','athletic',U,['athletic'],
    [10,14],[16,20],[11,15],[10,13],[11,14],[9,12],['parkour','climbing','agility_training','balance']))
NEW.append(occ('burglar_thief','Burglar / Pickpocket','criminal',U,['criminal'],
    [9,13],[15,19],[9,13],[12,16],[13,17],[9,13],['lockpicking','stealth','sleight_of_hand','perception']))
NEW.append(occ('smuggler','Smuggler','criminal',U,['criminal'],
    [10,14],[11,15],[11,15],[12,16],[14,18],[8,12],['driving','deception','firearms','navigation']))
NEW.append(occ('bouncer','Club Bouncer / Security','combat',U,['security'],
    [14,18],[9,13],[14,18],[8,12],[9,12],[9,13],['melee','intimidation','observation']))
NEW.append(occ('diver_professional','Professional Diver','athletic',U,['maritime','athletic'],
    [11,15],[13,17],[13,17],[10,14],[10,14],[9,13],['diving','survival','perception','swimming']))
NEW.append(occ('hunter_outdoorsman','Hunter / Outdoorsman','athletic',U,['outdoor'],
    [12,16],[13,17],[13,17],[10,14],[13,17],[8,12],['survival','navigation','firearms','tracking','perception']))
NEW.append(occ('sailor','Sailor','working',U,['maritime'],
    [11,15],[11,15],[12,16],[10,14],[11,15],[8,12],['sailing','navigation','survival','swimming','knot_tying']))
NEW.append(occ('bodyguard','Bodyguard','combat',U,['security','combat'],
    [14,18],[12,16],[14,18],[11,15],[10,14],[10,14],['firearms','melee','perception','tactics','close_protection']))
NEW.append(occ('private_security','Private Security Contractor','combat',U,['military','security'],
    [12,16],[12,16],[12,16],[11,15],[9,13],[9,13],['firearms','tactics','melee','surveillance']))
NEW.append(occ('forensic_technician','Forensic Technician','investigative',U,['investigation','science'],
    [7,11],[10,14],[8,12],[15,19],[11,15],[11,15],['evidence_collection','analysis','photography','lab_technique','observation']))
NEW.append(occ('stunt_performer','Stunt Performer','athletic',U,['athletic','entertainment'],
    [11,15],[16,20],[12,16],[9,13],[14,18],[9,13],['agility_training','climbing','driving','body_control','risk_assessment']))
NEW.append(occ('nursing_student','Nursing Student','medical',U,['medical','student'],
    [8,12],[10,14],[9,13],[12,16],[10,14],[11,15],['firstaid','patient_care','anatomy_basic']))
NEW.append(occ('marine_biologist','Marine Biologist','academic',U,['science','maritime'],
    [9,13],[10,14],[10,14],[14,17],[9,13],[11,15],['marine_biology','diving','research','perception']))
NEW.append(occ('psychologist','Clinical Psychologist','medical',U,['medical','academic'],
    [6,10],[8,12],[8,12],[14,18],[10,14],[16,20],['psychology','therapy','perception','persuasion','diagnosis']))
NEW.append(occ('farmer_owner','Farmer (Landowner)','working',U,['agriculture'],
    [12,16],[9,13],[13,17],[10,14],[11,15],[8,12],['farming','animal_handling','survival','equipment_operation']))
NEW.append(occ('clergy','Priest / Clergy','academic',U,['religious'],
    [6,10],[7,11],[8,12],[12,16],[11,15],[16,20],['counseling','persuasion','scripture_knowledge','public_speaking','empathy']))
NEW.append(occ('taxi_driver','Taxi Driver','working',U,['transport'],
    [8,12],[9,13],[9,13],[9,13],[11,15],[9,13],['driving','navigation','city_knowledge','customer_service']))

# Rare additions
R = 'rare'
NEW.append(occ('archaeologist','Archaeologist','academic',R,['science','exploration'],
    [9,13],[10,14],[10,14],[14,18],[11,15],[10,14],['archaeology','research','survival','navigation','perception']))
NEW.append(occ('social_worker','Social Worker','academic',R,['professional','helping'],
    [7,11],[9,13],[9,13],[12,16],[10,14],[15,19],['counseling','case_management','crisis_intervention','advocacy','perception']))
NEW.append(occ('boxer_professional','Professional Boxer','combat',R,['athletic','combat'],
    [15,19],[11,15],[14,18],[8,12],[9,13],[9,13],['boxing','endurance_training','strike_precision','footwork']))
NEW.append(occ('mma_fighter','MMA Fighter','combat',R,['athletic','combat'],
    [14,18],[14,18],[13,17],[9,13],[9,13],[10,14],['mma','grappling','striking','ground_fighting','endurance']))

# ── NEGATIVE / SPECIAL (very_rare — low-status or self-destructive) ──
# These are very unlikely draws. Put at very_rare and legendary.
N = 'very_rare'
NEW.append(occ('neet','NEET (Not in Education/Employment/Training)','negative',N,['negative','unemployed'],
    [6,10],[7,11],[7,11],[8,12],[6,10],[7,11],['isolation','internet_culture','gaming']))
NEW.append(occ('homeless','Homeless/Vagrant','negative',N,['negative','unemployed'],
    [8,12],[8,12],[9,13],[7,11],[6,10],[7,11],['survival_basic','shelter_finding','panhandling']))
NEW.append(occ('drug_addict','Drug Addict','negative',N,['negative','addiction'],
    [7,11],[7,11],[6,10],[8,12],[5,9],[6,10],['drug_knowledge','deception','survival_basic']))
NEW.append(occ('alcoholic','Chronic Alcoholic','negative',N,['negative','addiction'],
    [8,12],[7,11],[7,11],[9,13],[5,9],[7,11],['alcohol_tolerance','deception','survival_basic']))
NEW.append(occ('convict_former','Former Convict (Released)','negative',N,['negative','criminal'],
    [10,14],[10,14],[10,14],[9,13],[8,12],[8,12],['survival_basic','deception','street_smarts']))
NEW.append(occ('prison_inmate','Prison Inmate (Current)','negative',N,['negative','criminal'],
    [11,15],[10,14],[11,15],[9,13],[7,11],[8,12],['survival','intimidation','melee_basic','contraband']))
NEW.append(occ('hikikomori','Hikikomori/Shut-In','negative',N,['negative','isolated'],
    [5,9],[6,10],[6,10],[10,14],[6,10],[6,10],['internet','gaming','isolation']))
NEW.append(occ('gambling_addict','Chronic Gambler (Degenerate)','negative',N,['negative','addiction'],
    [7,11],[8,12],[8,12],[10,14],[4,8],[8,12],['gambling','deception','mathematics_basic']))
NEW.append(occ('bankrupt','Bankrupt/Destitute','negative',N,['negative','unemployed'],
    [7,11],[8,12],[8,12],[10,14],[5,9],[7,11],['survival_basic','deception','street_smarts']))
NEW.append(occ('stalker','Obsessive Stalker','negative',N,['negative','criminal'],
    [8,12],[11,15],[9,13],[11,15],[8,12],[7,11],['stalking','surveillance','stealth','obsession']))

# Negative @ legendary tier
L = 'legendary'
NEW.append(occ('brainwashed','Brainwashed Asset','negative',L,['negative','damaged'],
    [9,13],[9,13],[9,13],[10,14],[6,10],[8,12],['deception','sleeper_training','programming']))
NEW.append(occ('death_row','Death Row Inmate','negative',L,['negative','criminal'],
    [12,16],[11,15],[12,16],[10,14],[6,10],[9,13],['violence','survival','intimidation','no_fear_of_death']))
NEW.append(occ('severe_mentally_ill','Severely Mentally Ill (Untreated)','negative',L,['negative','medical'],
    [7,11],[8,12],[8,12],[9,13],[4,8],[5,9],['unpredictability','survival_basic','crisis_behavior']))

# ════════════════════════════════════════════════════════════════
# Read existing team-gen.json, replace occupations
# ════════════════════════════════════════════════════════════════

with open(TEAM_GEN, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check count
skill_occupations = [o for o in NEW if o['rarity'] in ('common','uncommon','rare')]
print(f"Common: {sum(1 for o in NEW if o['rarity']=='common')}")
print(f"Uncommon: {sum(1 for o in NEW if o['rarity']=='uncommon')}")
print(f"Rare: {sum(1 for o in NEW if o['rarity']=='rare')}")
print(f"Very Rare: {sum(1 for o in NEW if o['rarity']=='very_rare')}")
print(f"Legendary: {sum(1 for o in NEW if o['rarity']=='legendary')}")
print(f"Total: {len(NEW)}")

# Sort by rarity for cleaner output
rarity_order = {'legendary':0,'very_rare':1,'rare':2,'uncommon':3,'common':4}
NEW.sort(key=lambda o: rarity_order.get(o['rarity'],99))

data['occupations'] = NEW

# Also replace the guide_occupations? No — guides are always experienced, keep separate.
# Add note about rarity system
data['_occupation_note'] = 'Occupations now use rarity tiers: common(40%)/uncommon(30%)/rare(16%)/very_rare(10%)/legendary(4%). Negative/special occupations are in very_rare and legendary tiers.'

with open(TEAM_GEN, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nWritten {len(NEW)} occupations to {TEAM_GEN}")
