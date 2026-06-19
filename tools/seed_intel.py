"""Seed intel[] array into game.json. Safe to re-run — skips if already present."""
import json

path = 'data/game.json'
with open(path, encoding='utf-8-sig') as f:
    d = json.load(f)

if 'intel' not in d:
    d['intel'] = [
        {
            "id": "memo-lockdown-order",
            "type": "memo",
            "title": "Facility Lockdown — Internal Order",
            "found_in": "B1 Floor / Notice Board",
            "timestamp": "06:14",
            "content": "TO: ALL PERSONNEL\nFROM: Director Wesker\nSUBJECT: BIOHAZARD PROTOCOL DELTA\n\nEffective immediately: Facility lockdown is in effect. All staff are to report to designated safe zones. Non-essential personnel must not access sublevel B3 under any circumstances.\n\nT-virus containment breach has been confirmed in Lab Section B3-C. Umbrella rapid-response team is inbound. ETA: 90 minutes.\n\nDo NOT attempt self-evacuation. The situation is CONTAINED.\n\n— Wesker"
        },
        {
            "id": "log-security-checkpoint",
            "type": "log",
            "title": "Checkpoint Security Log — 06:09",
            "found_in": "B1 Checkpoint / Security Log",
            "timestamp": "06:09",
            "content": "05:47 — Shift change. Team Alpha taking over from Team Bravo.\n05:52 — Routine ID checks. All personnel accounted for.\n06:04 — Unusual noise from ventilation shaft B3-V7. Logged and reported up chain.\n06:09 — Dispatching two-man team to investigate sublevel B3. All quiet on our end.\n\n[ENTRY ENDS HERE — subsequent pages missing]"
        },
        {
            "id": "research-tvirus-mutation",
            "type": "research",
            "title": "T-Virus Mutation Rate — Preliminary Notes",
            "found_in": "B3 Lab / Research Terminal",
            "timestamp": "04:33",
            "content": "Subject: Accelerated mutation observed in test batch 7-G\nResearcher: Dr. Ashford\n\nMutation rate in the current batch has exceeded projected parameters by 340%. The standard 72-hour incubation window no longer applies. We are seeing full transition in under 6 hours at ambient temperature.\n\nCritical note: The Licker strain (designation: HCF) appears to retain significantly higher cognitive function than previous variants. Avoid direct engagement. Standard security countermeasures are INSUFFICIENT.\n\nRecommend immediate escalation to Director level. This is no longer a contained test."
        }
    ]
    print("Seeded intel with 3 sample documents.")
else:
    print(f"intel[] already exists ({len(d['intel'])} entries). No changes made.")

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print('Done.')
