"""Stress-test the fixed character generator."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'tools')

from character_generator import generate_npc

N = 200
results, errors = [], []
for i in range(N):
    try:
        results.append(generate_npc())
    except Exception as e:
        errors.append(f'#{i}: {e}')

print(f'Generated: {len(results)}/{N}  Errors: {len(errors)}')
if errors:
    for e in errors[:5]:
        print(' ERR:', e)

skill_counts = [len(c['skills']) for c in results]
weak_counts  = [len(c['weaknesses']) for c in results]
all_strs = [c['strength'] for c in results]
over19 = [c['name'] for c in results
          if not any(t in c.get('occupation_tags',[]) for t in ['enhanced','superhuman','experimental','divine','monster'])
          and any(c[s] > 19 for s in ['strength','agility','endurance','intelligence','luck','psyche_force'])]

has_value = sum(1 for c in results for v in c['skills'].values() if 'value' in v)
total_skills = sum(skill_counts)
has_orient = sum(1 for c in results if c.get('sexual_orientation'))

sources = {'occupation': 0, 'hobby': 0, 'background': 0}
for c in results:
    for v in c['skills'].values():
        src = v.get('source', '?')
        sources[src] = sources.get(src, 0) + 1

nats = {}
for c in results:
    nats[c['nationality']] = nats.get(c['nationality'], 0) + 1

print(f'\nStats:')
print(f'  Skills:          min={min(skill_counts)} max={max(skill_counts)} avg={sum(skill_counts)/N:.1f}')
print(f'  Weaknesses:      min={min(weak_counts)} max={max(weak_counts)} avg={sum(weak_counts)/N:.1f}')
print(f'  STR:             min={min(all_strs)} max={max(all_strs)} avg={sum(all_strs)/N:.1f}')
print(f'  Over-19 (normal):{len(over19)} chars')
print(f'  numeric values:  {has_value}/{total_skills} skills')
print(f'  sexual_orient:   {has_orient}/{N}')
print(f'  skill sources:   {sources}')
print(f'\nTop 8 nationalities: {sorted(nats.items(), key=lambda x:-x[1])[:8]}')

# Distribution of weakness counts
wdist = {}
for w in weak_counts:
    wdist[w] = wdist.get(w, 0) + 1
print(f'\nWeakness distribution: {dict(sorted(wdist.items()))}')

# Sample character summary
c = results[0]
print(f'\nSample: {c["name"]} ({c["nationality"]}, {c["occupation"]})')
print(f'  {len(c["skills"])} skills | {len(c["weaknesses"])} weaknesses | orientation: {c.get("sexual_orientation")}')
skill_vals = [(k, v["value"]) for k, v in c["skills"].items() if "value" in v]
skill_vals.sort(key=lambda x: -x[1])
print(f'  Best skills: {skill_vals[:4]}')
