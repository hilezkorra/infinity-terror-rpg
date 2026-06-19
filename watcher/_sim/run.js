// Simulation harness: 50 actions when Igor notices a Licker.
// For each action it restores an identical baseline, appends the GM's event
// line(s), runs ONE real watcher tick, and captures the watcher's cron output.
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const SIM = __dirname;
const ROOT = SIM.replace(/\\/g, '/');
const WATCHER = path.join(SIM, '..', 'watcher.js');
const dataDir = path.join(SIM, 'data');
const savesDir = path.join(SIM, 'saves');
const snapDir = path.join(SIM, '_snap');

// ── config ──
const cfg = JSON.parse(fs.readFileSync(path.join(SIM, '..', 'config.json'), 'utf8'));
cfg.settings.project_dir = ROOT;
cfg.settings.auto_gm = false;
fs.mkdirSync(dataDir, { recursive: true });
fs.mkdirSync(savesDir, { recursive: true });
fs.writeFileSync(path.join(SIM, 'config.json'), JSON.stringify(cfg, null, 2));

// ── baseline game state ──
const baseGame = {
  phase: 'movie', points: 1000, deaths: 0,
  character: {
    name: 'Igor', rank: 'D', level: 6, xp: 1500,
    hp: 200, hp_max: 240,
    strength: 18, agility: 20, endurance: 16, intelligence: 14, luck: 11, psyche_force: 0,
    skills: { sneak:{level:'skilled'}, aim:{level:'expert'}, melee:{level:'skilled'},
              perception:{level:'novice'}, athletics:{level:'skilled'}, climb:{level:'skilled'} },
    weapons: [{name:'Desert Eagle', id:40, ammo:21}, {name:'Combat Knife', id:41, status:[]}],
    items: [{name:'First Aid Kit', id:50, status:[]}, {name:'Flashbang', id:51, status:[]}, {name:'Adrenaline', id:52, status:[]}],
    status_effects: [], fear_meter: 30, fear_level: 'Tense'
  },
  guide: { name:'Vera', alive:true, rank:'E', hp:150, hp_max:150, strength:12, agility:14, status_effects:[] },
  team: { members: [ { name:'Rookie', rank:'Unranked', hp:100, hp_max:100, strength:10, agility:10, status:'Active', status_effects:[] } ] },
  combat: { active:false, enemies:[] },
  watcher: { last_processed_event_id:0, checkpoint_event_id:0 }
};

const env = Object.assign({}, process.env, { TI_CONFIG: path.join(SIM, 'config.json') });
function tick() { execSync(`node "${WATCHER}" --once`, { env, stdio:'ignore' }); }
function readLog() { return fs.existsSync(path.join(dataDir,'event-log.txt')) ? fs.readFileSync(path.join(dataDir,'event-log.txt'),'utf8').split('\n').map(s=>s.trim()).filter(Boolean) : []; }

// ── build baseline: checkpoint (God's Domain) + Licker registered ──
fs.writeFileSync(path.join(dataDir,'game.json'), JSON.stringify(baseGame,null,2));
fs.writeFileSync(path.join(dataDir,'chat.json'), JSON.stringify({status:'waiting_for_player',messages:[{id:1,sender:'system',content:'init'}]},null,2));
fs.writeFileSync(path.join(dataDir,'event-log.txt'),
  'System Message[ID:1]: Character "Igor" enters Gods Domain. All injuries healed, and negative status effects removed;\n' +
  'System Message[ID:2]: Enemy "Licker[ID:1]" appears. Rank C. HP 200. Combat +8.\n');
tick();
// snapshot baseline
if (fs.existsSync(snapDir)) fs.rmSync(snapDir,{recursive:true,force:true});
fs.mkdirSync(snapDir,{recursive:true});
for (const f of ['data/game.json','data/chat.json','data/event-log.txt','saves/checkpoint.json','saves/checkpoint-chat.json']) {
  const src = path.join(SIM,f); if (fs.existsSync(src)) { fs.mkdirSync(path.dirname(path.join(snapDir,f)),{recursive:true}); fs.copyFileSync(src, path.join(snapDir,f)); }
}
const baselineLog = readLog();
const baseMaxId = baselineLog.reduce((m,l)=>{const x=l.match(/\[ID:(\d+)\]/);return x?Math.max(m,+x[1]):m;},0);

function restore() {
  for (const f of ['data/game.json','data/chat.json','data/event-log.txt','saves/checkpoint.json','saves/checkpoint-chat.json']) {
    const snap = path.join(snapDir,f), dst = path.join(SIM,f);
    if (fs.existsSync(snap)) fs.copyFileSync(snap,dst);
  }
}

// ── 50 scenarios. Each: {cat,label, ev:[...event texts...]} ──
const S = [
  // PERCEPTION / AWARENESS
  ['Perception','Listen for the Licker', ['Character "Igor" tries to perceive the Licker\'s position. Difficulty 15. [skill:perception]']],
  ['Perception','Analyse its anatomy for a weak point', ['Character "Igor" tries to analyse the Licker\'s weak points. Difficulty 20. [INT]']],
  ['Perception','Scan the room for an exit', ['Character "Igor" tries to spot an escape route. Difficulty 12. [INT]']],
  // STEALTH
  ['Stealth','Sneak past (it hunts by sound) — lethal', ['Character "Igor" tries to sneak past the Licker. Difficulty 25. [lethal][skill:sneak]']],
  ['Stealth','Freeze and hold breath', ['Character "Igor" tries to stay perfectly still and silent. Difficulty 18. [END]']],
  ['Stealth','Retreat over broken glass — disadvantage', ['Character "Igor" tries to retreat silently over glass. Difficulty 20. [disadvantage][skill:sneak]']],
  // RANGED COMBAT (opposed)
  ['Ranged','Snap-shot with the Desert Eagle', ['Character "Igor" attacks "Licker[ID:1]" with 45 damage.']],
  ['Ranged','Aimed shot at the exposed brain (hard check)', ['Character "Igor" tries to land a precise shot on the Licker\'s brain. Difficulty 30. [AGI][skill:aim]']],
  ['Ranged','Heavy shotgun blast', ['Character "Igor" attacks "Licker[ID:1]" with 70 damage.']],
  // MELEE (opposed)
  ['Melee','Stab with the combat knife', ['Character "Igor" attacks "Licker[ID:1]" with 18 damage.']],
  ['Melee','Licker turn: it lunges at Igor', ['Enemy "Licker[ID:1]" attacks "Igor".']],
  ['Melee','Licker turn: tongue-strike at Rookie', ['Enemy "Licker[ID:1]" attacks "Rookie".']],
  // ITEMS
  ['Item','Throw a flashbang', ['Character "Igor" uses item "Flashbang[ID:51]";']],
  ['Item','Inject adrenaline (temp stats)', ['Character "Igor" uses item "Adrenaline[ID:52]";','Character "Igor" gains 8 STR;','Character "Igor" gains 8 AGI;']],
  ['Item','Use first aid kit', ['Character "Igor" uses item "First Aid Kit[ID:50]";','Character "Igor" gains 50 HP;']],
  ['Item','Knife breaks on its hide', ['Item "Combat Knife[ID:41]" has gained status "broken";']],
  // MOVEMENT / ATHLETICS
  ['Move','Vault over a desk', ['Character "Igor" tries to vault the desk. Difficulty 12. [skill:athletics]']],
  ['Move','Leap a collapsed-floor gap — lethal', ['Character "Igor" tries to leap the floor gap. Difficulty 22. [lethal][skill:athletics]']],
  ['Move','Sprint the corridor (Licker is fast)', ['Character "Igor" tries to outrun the Licker to the door. Difficulty 28. [AGI]']],
  ['Move','Climb to the catwalk', ['Character "Igor" tries to climb to the catwalk. Difficulty 14. [STR][skill:climb]']],
  // ENVIRONMENT / CLEVER
  ['Environ','Shoot a chain to drop a crate on it', ['Character "Igor" tries to shoot the chain holding the crate. Difficulty 18. [AGI][skill:aim]']],
  ['Environ','Bait it onto live wires', ['Character "Igor" tries to lure the Licker onto the live wires. Difficulty 20. [INT]']],
  ['Environ','Barricade the door', ['Character "Igor" tries to barricade the door in time. Difficulty 16. [STR]']],
  ['Environ','Force a jammed blast door (DC 100)', ['Character "Igor" tries to force the jammed blast door. Difficulty 100. [STR]']],
  // SPECIAL ROLL MODES
  ['Special','Hack the lock, must-succeed [floor:10]', ['Character "Igor" tries to hack the door lock. Difficulty 18. [floor:10][no-skill][INT]']],
  ['Special','Survive a ceiling collapse — pure fate [raw]', ['Character "Igor" tries to survive the ceiling collapse. Difficulty 12. [raw]']],
  ['Special','Find a weapon in the dark [d100]', ['Character "Igor" tries to find a working weapon in the dark. Difficulty 60. [d100][INT]']],
  ['Special','Guess the keypad code [range:1-100]', ['Character "Igor" tries to guess the keypad code. Difficulty 70. [range:1-100]']],
  ['Special','Wrestle it bare-handed (DC 250, [d1000])', ['Character "Igor" tries to physically pin the Licker. Difficulty 250. [STR][d1000]']],
  ['Special','Spot it from high ground [advantage]', ['Character "Igor" tries to spot the Licker from above. Difficulty 16. [advantage][skill:perception]']],
  // STATUS EFFECTS
  ['Status','Its shriek disorients Igor', ['Character "Igor" gets temporary status effect "Disoriented";']],
  ['Status','Gains a permanent trait', ['Character "Igor" gets permanent status effect "Adrenaline-Resistant";']],
  ['Status','Shake off the disorientation', ['Character "Igor" gets temporary status effect "Disoriented";','Character "Igor" loses status effect "Disoriented";']],
  ['Status','Splashed by acidic blood (poison + dmg)', ['Character "Igor" gets temporary status effect "Poisoned";','Character "Igor" loses 15 HP;']],
  // DAMAGE / HP STATES
  ['Damage','Heavy claw swipe (→ Bloodied)', ['Character "Igor" loses 90 HP;']],
  ['Damage','Gored low (→ Mortally Wounded)', ['Character "Igor" loses 175 HP;']],
  ['Damage','Permanent max-HP from rank training', ['Character "Igor" gains 50 MaxHP permanently;']],
  // PROGRESSION
  ['Progress','XP for wounding it (level check)', ['Character "Igor" gains 400 XP;']],
  ['Progress','Earn survival points', ['Character "Igor" gains 300 points;']],
  ['Progress','Permanent strength surge', ['Character "Igor" gains 4 STR permanently;']],
  ['Progress','Learn a new skill (boundary case)', ['Character "Igor" learns skill "Demolitions" at beginner;']],
  // LUCK (low-power so it shows)
  ['Luck','Rookie holds the door (luck swing)', ['Character "Rookie" tries to hold the door shut. Difficulty 14. [STR]']],
  // OTHERS — no rewind
  ['NoRewind','Rookie shoots it (can\'t hurt C-rank)', ['Character "Rookie" attacks "Licker[ID:1]" with 40 damage.']],
  ['NoRewind','Rookie is killed (teammate — NO rewind)', ['Character "Rookie" has died;']],
  ['NoRewind','Vera (guide) strikes it', ['Character "Vera" attacks "Licker[ID:1]" with 45 damage.']],
  ['NoRewind','Vera (guide) dies (NO rewind)', ['Character "Vera" has died;']],
  // PROTAGONIST DEATH — rewind
  ['Rewind','Decapitated — protagonist death', ['Character "Igor" has died. Rewind to last checkpoint;']],
  ['Rewind','Bleeds out to 0 HP (auto-death)', ['Character "Igor" loses 300 HP;']],
  // CLASH
  ['Clash','A horde joins — whole-team clash', ['Enemy "Zombie Horde[ID:2]" appears. Rank F. HP 30. x20.','Clash: the team engages the Zombie Horde.']],
  ['Clash','Scoped: Igor+Vera hold, Rookie flees', ['Enemy "Zombie Horde[ID:3]" appears. Rank F. HP 30. x20.','Clash: [Igor, Vera] vs Zombie Horde.']],
];

// ── run ──
const out = [];
S.forEach((sc, i) => {
  restore();
  const before = readLog();
  let maxId = before.reduce((m,l)=>{const x=l.match(/\[ID:(\d+)\]/);return x?Math.max(m,+x[1]):m;},0);
  // append GM events
  let append = '';
  sc[2].forEach(ev => { maxId++; append += `System Message[ID:${maxId}]: ${ev}\n`; });
  fs.appendFileSync(path.join(dataDir,'event-log.txt'), append);
  tick();
  const after = readLog();
  const beforeSet = new Set(before);
  const diff = after.filter(l => !beforeSet.has(l));
  const cron = diff.filter(l => /^Cron Message/i.test(l)).map(l => l.replace(/^Cron Message\[ID:\d+\]:\s*/i,''));
  out.push({ n:i+1, cat:sc[0], label:sc[1], gm:sc[2], cron });
});

// ── print ──
out.forEach(r => {
  console.log(`\n#${r.n} [${r.cat}] ${r.label}`);
  r.gm.forEach(g => console.log(`   GM →  ${g}`));
  if (r.cron.length) r.cron.forEach(c => console.log(`   WATCH ◄  ${c}`));
  else console.log(`   WATCH ◄  (no watcher handler — GM edits game.json directly)`);
});
fs.rmSync(snapDir,{recursive:true,force:true});
