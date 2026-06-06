#!/usr/bin/env node
/**
 * TERROR INFINITY — WATCHER ENGINE
 * --------------------------------------------------------------
 * The mechanical brain of the game. Watches data/event-log.txt and
 * data/chat.json. Applies all math (HP, XP, levels, dice, status,
 * inventory), handles checkpoints + death-rewind, and (optionally)
 * dispatches player messages to the Claude CLI as the GM.
 *
 * The AI writes INTENT events. This watcher computes RESULTS.
 *
 * Run:  node watcher.js
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// ── Load config ───────────────────────────────────────────────
const CONFIG_PATH = process.env.TI_CONFIG || path.join(__dirname, 'config.json');
const CFG = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
const ROOT = CFG.settings.project_dir || path.join(__dirname, '..');

const P = {
  game:        path.join(ROOT, 'data', 'game.json'),
  chat:        path.join(ROOT, 'data', 'chat.json'),
  eventLog:    path.join(ROOT, 'data', 'event-log.txt'),
  checkpoint:  path.join(ROOT, 'saves', 'checkpoint.json'),
  chkChat:     path.join(ROOT, 'saves', 'checkpoint-chat.json'),
  watcherLog:  path.join(ROOT, CFG.settings.log_file || 'watcher/watcher.log'),
  gmLog:       path.join(ROOT, CFG.settings.gm_log_file || 'watcher/gm.log'),
};

const LEVEL_UP_HP_BONUS = CFG.level_up_hp_bonus ?? 5;

// ── Logging ───────────────────────────────────────────────────
function log(...a) {
  const line = `[${new Date().toISOString()}] ${a.join(' ')}`;
  console.log(line);
  try { fs.appendFileSync(P.watcherLog, line + '\n'); } catch (e) {}
}

// ── JSON helpers (tolerant of mid-write reads) ────────────────
function readJsonSafe(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (e) { return null; }
}
function writeJson(file, data) {
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
  fs.renameSync(tmp, file); // atomic-ish swap so readers never see half a file
}

// ── Event log helpers ─────────────────────────────────────────
const LINE_RE = /^(System|Cron)\s+Message(?:\s*\[ID:\s*(\d+)\])?\s*:\s*(.*)$/i;

function readEventLines() {
  let txt = '';
  try { txt = fs.readFileSync(P.eventLog, 'utf8'); } catch (e) { return []; }
  return txt.split('\n').map(l => l.trim()).filter(Boolean).map(raw => {
    const m = raw.match(LINE_RE);
    if (!m) return { id: null, source: 'unknown', text: raw, raw };
    return { id: m[2] ? parseInt(m[2], 10) : null, source: m[1].toLowerCase(), text: m[3], raw };
  });
}
function maxEventId(lines) {
  return lines.reduce((mx, l) => (l.id && l.id > mx ? l.id : mx), 0);
}
function appendCron(text, id) {
  fs.appendFileSync(P.eventLog, `Cron Message[ID:${id}]: ${text}\n`);
}
function truncateEventLogTo(maxKeepId) {
  const lines = readEventLines();
  const kept = lines.filter(l => l.id == null || l.id <= maxKeepId).map(l => l.raw);
  fs.writeFileSync(P.eventLog, kept.join('\n') + (kept.length ? '\n' : ''));
}

// ── Character resolution ──────────────────────────────────────
// Returns the live object so mutations persist when we write game.json.
function resolveChar(game, name) {
  if (!name) return null;
  const n = name.trim().toLowerCase();
  if (game.character && (game.character.name || '').toLowerCase() === n)
    return { ref: game.character, type: 'player' };
  if (game.guide && (game.guide.name || '').toLowerCase() === n)
    return { ref: game.guide, type: 'guide' };
  const m = (game.team?.members || []).find(x => (x.name || '').toLowerCase() === n);
  if (m) return { ref: m, type: 'member' };
  const npc = (game.npcs || []).find(x => (x.name || '').toLowerCase() === n);
  if (npc) return { ref: npc, type: 'npc' };
  return null;
}

function allChars(game, includeDead) {
  const out = [];
  if (game.character?.name) out.push({ ref: game.character, type: 'player' });
  if (game.guide?.name && (includeDead || game.guide.alive !== false)) out.push({ ref: game.guide, type: 'guide' });
  (game.team?.members || []).forEach(m => { if (includeDead || (m.hp ?? 1) > 0) out.push({ ref: m, type: 'member' }); });
  (game.npcs || []).forEach(n => { if (includeDead || n.alive !== false) out.push({ ref: n, type: 'npc' }); });
  return out;
}

// ── Stat / skill helpers ──────────────────────────────────────
function statValue(ch, statName) {
  const map = { str: 'strength', agi: 'agility', end: 'endurance', int: 'intelligence',
                luck: 'luck', psy: 'psyche_force', psyche: 'psyche_force' };
  const key = map[statName.toLowerCase()] || statName.toLowerCase();
  return ch[key] ?? 0;
}
// D&D-style ability modifier: score 10 = +0, 14 = +2, 20 = +5, 30 = +10.
function abilityMod(score) { return Math.floor((score - 10) / 2); }

// Power multiplier from rank — this is what scales rolls to DC 100/1000.
function powerForRank(rank) {
  const key = String(rank || 'unranked').toLowerCase().trim();
  return (CFG.rank_power && CFG.rank_power[key]) ?? 1;
}
function charPower(c) { return powerForRank(c.rank); }

// Combat modifier for a combatant (characters use STR/AGI ability mod + a skill if any).
function combatMod(c) {
  if (c.combat_mod != null) return c.combat_mod; // enemies can carry an explicit mod
  const best = Math.max(abilityMod(c.strength ?? 10), abilityMod(c.agility ?? 10));
  return best + skillBonus(c, 'melee');
}

// One opposed-roll side: returns {die, total, power, mod, nat1, nat20}
function rollSide(c, size, modOverride) {
  const mod = modOverride != null ? modOverride : combatMod(c);
  const power = charPower(c);
  const die = rollDie(size);
  return { die, mod, power, total: (die + mod) * power, nat1: die === 1, nat20: die === size };
}
function skillBonus(ch, skillName) {
  if (!ch.skills || !skillName) return 0;
  const sk = ch.skills[skillName.toLowerCase()];
  if (!sk) return 0;
  if (typeof sk === 'number') return sk;
  if (sk.bonus != null) return sk.bonus;
  const lvl = (sk.level || 'untrained').toLowerCase();
  return CFG.skill_proficiency_bonus[lvl] ?? 0;
}

// ── Status effect helpers (strings or {name,permanent,negative}) ─
function hasStatus(ch, name) {
  return (ch.status_effects || []).some(s => (typeof s === 'string' ? s : s.name).toLowerCase() === name.toLowerCase());
}
function addStatus(ch, name, opts = {}) {
  ch.status_effects = ch.status_effects || [];
  if (hasStatus(ch, name)) return;
  ch.status_effects.push({ name, permanent: !!opts.permanent, negative: opts.negative !== false });
}
function removeStatus(ch, name) {
  ch.status_effects = (ch.status_effects || []).filter(s =>
    (typeof s === 'string' ? s : s.name).toLowerCase() !== name.toLowerCase());
}

// ── XP / level ────────────────────────────────────────────────
function levelForXp(xp) {
  const base = CFG.xp_curve_base || 50;
  let lvl = 1;
  for (let L = 1; L <= (CFG.max_level || 40); L++) {
    const threshold = base * (L - 1) * L;
    if (xp >= threshold) lvl = L; else break;
  }
  return lvl;
}

// ── Fear ──────────────────────────────────────────────────────
function fearLevelFor(v) {
  const lv = (CFG.fear_levels || []).find(f => v <= f.max);
  return lv || { name: 'Calm', multiplier: 1.0 };
}

// ── DICE ENGINE ───────────────────────────────────────────────
function rollDie(size) { return Math.floor(Math.random() * size) + 1; }

function processRoll(game, name, line, nextId, cron) {
  const ch = resolveChar(game, name);
  if (!ch) { cron.push(`Roll ignored — unknown character "${name}".`); return; }
  const c = ch.ref;

  // Difficulty
  const diffM = line.match(/Difficulty(?:\s+Threshold)?\s+(\d+)/i);
  if (!diffM) { cron.push(`Roll for "${name}" ignored — no Difficulty found.`); return; }
  const DC = parseInt(diffM[1], 10);

  // Tags
  const lethal   = /\[lethal\]/i.test(line) || CFG.dice.nat1_lethal_default;
  const adv       = /\[advantage\]/i.test(line);
  const dis       = /\[disadvantage\]/i.test(line);
  const raw        = /\[raw\]/i.test(line);       // no modifiers at all
  const noSkill   = /\[no-?skill\]/i.test(line);  // stat only, no proficiency
  const statTag   = (line.match(/\[(STR|AGI|END|INT|LUCK|PSY)\]/i) || [])[1];
  const skillTag  = (line.match(/\[skill:\s*([a-z0-9_\- ]+)\]/i) || [])[1];
  const dieTag    = (line.match(/\[d(\d+)\]/i) || [])[1];               // [d100], [d1000]
  const floorTag  = (line.match(/\[floor:\s*(\d+)\]/i) || [])[1];        // [floor:10] reroll until >=
  const rangeTag  = line.match(/\[range:\s*(\d+)\s*-\s*(\d+)\]/i);       // [range:50-100]
  const actionM   = line.match(/tries to\s+([^.\[]+)|attempts(?:\s+to)?\s+([^.\[]+)/i);
  const action    = ((actionM && (actionM[1] || actionM[2])) || 'act').trim();

  // Determine modifier
  let stat = statTag ? statTag.toLowerCase()
           : (skillTag ? (CFG.skill_stat_map[skillTag.toLowerCase()] || CFG.default_skill_stat)
                       : (CFG.skill_stat_map[action.split(' ')[0].toLowerCase()] || CFG.default_skill_stat));
  let modifier = 0;
  if (!raw) {
    const statRaw = statValue(c, stat);
    // 'dnd' (default): floor((stat-10)/2) keeps the d20 meaningful.
    // 'flat': add the whole stat (old behaviour) — power-fantasy, randomness fades.
    const mode = (CFG.dice.modifier_mode || 'dnd').toLowerCase();
    modifier += (mode === 'flat') ? statRaw : abilityMod(statRaw);
    if (!noSkill) {
      const skName = skillTag || action.split(' ')[0];
      modifier += skillBonus(c, skName);
    }
  }

  // Die size — default d20, or forced bigger by story ([d100], [d1000])
  const size = dieTag ? parseInt(dieTag, 10) : (CFG.dice.die_size || 20);
  const power = raw ? 1 : charPower(c);

  // Roll modes
  let die, attempts = 1;
  if (rangeTag) {
    // [range:A-B] — System dictates a flat random number in a band (no modifier/power)
    const lo = parseInt(rangeTag[1], 10), hi = parseInt(rangeTag[2], 10);
    const val = lo + Math.floor(Math.random() * (hi - lo + 1));
    const ok = val >= DC;
    cron.push(`Character "${name}" draws ${val} (range ${lo}-${hi}) vs Difficulty ${DC} — ${ok ? 'success' : 'failure'}.`);
    if (lethal && val === lo) { cron.push(`GM DIRECTIVE: lowest possible draw on a LETHAL check — fatal outcome for "${name}".`); applyDeath(game, name, c, ch.type, nextId, cron); }
    return;
  }
  if (floorTag) {
    // [floor:N] — reroll until the die meets the floor; report attempts (rising danger)
    const fl = parseInt(floorTag, 10);
    do { die = rollDie(size); attempts++; } while (die < fl && attempts < 100);
    attempts--; // correct count
  } else {
    die = rollDie(size);
    if (adv || dis) { const d2 = rollDie(size); die = (adv ? Math.max : Math.min)(die, d2); }
  }

  const nat1 = die === 1;
  const nat20 = die === size;
  const final = (die + modifier) * power;

  // Tier evaluation. Luck bands scale with power granularity so they stay meaningful
  // at every tier (at Power=1 this is the classic ±1 around the DC).
  const critHi = DC * (CFG.dice.crit_success_multiplier || 1.5);
  const critLo = DC * (CFG.dice.crit_fail_multiplier || 0.5);
  const margin = final - DC;
  let tier, luckDelta = 0, extra = null, death = false;

  if (nat1) {
    tier = 'CRITICAL FAILURE (natural 1)';
    if (lethal) death = true;
    extra = 'negative';
  } else if (nat20 && final < DC) {
    tier = 'success (natural 20 — pulled it off against the odds)';
  } else if (final >= critHi) {
    tier = 'OVERWHELMING SUCCESS';
    extra = 'positive';
  } else if (margin >= 0 && margin < power) {
    tier = 'borderline success'; luckDelta = +(CFG.dice.borderline_luck_gain || 1);
  } else if (margin < 0 && margin >= -power) {
    tier = 'near miss'; luckDelta = -(CFG.dice.fail_by_one_luck_loss || 1);
  } else if (final >= DC) {
    tier = 'success';
  } else if (final <= critLo) {
    tier = 'OVERWHELMING FAILURE'; extra = 'negative';
  } else {
    tier = 'failure';
  }

  const sign = modifier >= 0 ? '+' : '';
  const extras = [];
  if (adv) extras.push('advantage'); if (dis) extras.push('disadvantage');
  if (size !== 20) extras.push(`d${size}`);
  if (floorTag) extras.push(`floor ${floorTag} after ${attempts} attempt${attempts>1?'s':''}`);
  const tag = extras.length ? ` (${extras.join(', ')})` : '';
  const powStr = power !== 1 ? ` ×${power} power` : '';
  cron.push(`Character "${name}" rolls ${die}${tag}. Modifier ${sign}${modifier}${powStr}. Final result ${final} vs Difficulty ${DC} — ${tier}.`);
  if (floorTag && attempts > 3) cron.push(`GM DIRECTIVE: it took ${attempts} attempts for "${name}" to clear the floor — narrate the cost of that delay (noise, time, exposure, rising danger).`);

  // Luck adjustment
  if (luckDelta !== 0 && c.luck != null) {
    c.luck = Math.max(0, c.luck + luckDelta);
    cron.push(`Character "${name}" luck ${luckDelta > 0 ? 'increased' : 'decreased'} by ${Math.abs(luckDelta)} (now ${c.luck}).`);
  }
  // Extra-consequence flag for the GM
  if (extra === 'positive') cron.push(`GM DIRECTIVE: Narrate an EXTRA POSITIVE outcome for "${name}" (overwhelming success on "${action}").`);
  if (extra === 'negative' && !death) cron.push(`GM DIRECTIVE: Narrate an EXTRA NEGATIVE consequence for "${name}" (${nat1 ? 'critical failure' : 'overwhelming failure'} on "${action}").`);

  // Lethal natural 1
  if (death) {
    cron.push(`GM DIRECTIVE: Natural 1 on a LETHAL roll — "${name}" suffers a fatal outcome on "${action}".`);
    applyDeath(game, name, c, ch.type, nextId, cron);
  }
}

// ── COMBAT ────────────────────────────────────────────────────
// Enemies live in game.combat.enemies. They carry rank (-> power), combat_mod, hp, count.
function ensureCombat(game) { game.combat = game.combat || { active: false, enemies: [] }; return game.combat; }

function findEnemy(game, ref) {
  const cb = ensureCombat(game);
  const idM = ref.match(/\[ID:(\d+)\]/);
  const id = idM ? parseInt(idM[1], 10) : null;
  const bare = ref.replace(/\s*\[ID:\d+\]/, '').trim().toLowerCase();
  return cb.enemies.find(e => (id != null && e.id === id) || (e.name || '').toLowerCase() === bare && e.alive !== false);
}

// Resolve any combatant — a character (player/guide/member) or a registered enemy.
function resolveCombatant(game, ref) {
  const asChar = resolveChar(game, ref.replace(/\s*\[ID:\d+\]/, '').trim());
  if (asChar) return { ref: asChar.ref, type: asChar.type, isEnemy: false };
  const e = findEnemy(game, ref);
  if (e) return { ref: e, type: 'enemy', isEnemy: true };
  return null;
}

function registerEnemy(game, txt, cron) {
  const m = txt.match(/Enemy\s+"([^"]+?)(?:\[ID:(\d+)\])?"\s+appears/i);
  if (!m) return false;
  const cb = ensureCombat(game);
  const rank = (txt.match(/Rank\s+([A-Za-z]{1,3})\b/i) || [])[1] || 'unranked';
  const hp   = parseInt((txt.match(/HP\s+(\d+)/i) || [])[1] || '50', 10);
  const mod  = parseInt((txt.match(/Combat\s*\+?(\-?\d+)/i) || [])[1] || String(CFG.combat.default_enemy_mod), 10);
  const count= parseInt((txt.match(/(?:x|count\s+)(\d+)/i) || [])[1] || '1', 10);
  const id   = m[2] ? parseInt(m[2], 10) : (cb.enemies.reduce((mx,e)=>Math.max(mx,e.id||0),0) + 1);
  cb.active = true;
  cb.enemies.push({ name: m[1].trim(), id, rank: rank.toLowerCase(), combat_mod: mod, hp, hp_max: hp, count, alive: true });
  cron.push(`Enemy registered: "${m[1].trim()}[ID:${id}]" — Rank ${rank.toUpperCase()}, HP ${hp}${count>1?`, x${count}`:''}, power ×${powerForRank(rank)}.`);
  return true;
}

function damageEnemy(game, e, dmg, cron) {
  e.hp = Math.max(0, e.hp - dmg);
  if (e.hp <= 0) {
    if (e.count > 1) { e.count--; e.hp = e.hp_max; cron.push(`One "${e.name}" falls. ${e.count} remain.`); }
    else { e.alive = false; cron.push(`Enemy "${e.name}[ID:${e.id}]" has been killed.`); }
  } else {
    cron.push(`Enemy "${e.name}[ID:${e.id}]" takes ${dmg} damage (${e.hp}/${e.hp_max}).`);
  }
}

// Opposed attack: attacker (die+mod)*power vs defender (die+mod)*power.
function processAttack(game, txt, nextId, cron) {
  const m = txt.match(/"([^"]+?)"\s+attacks\s+"([^"]+?)"/i);
  if (!m) return false;
  const atk = resolveCombatant(game, m[1]);
  const def = resolveCombatant(game, m[2]);
  if (!atk || !def) { cron.push(`Attack ignored — combatant not found ("${m[1]}" → "${m[2]}").`); return true; }

  const dmgTag = parseInt((txt.match(/\b(\d+)\s*(?:dmg|damage)\b/i) || [])[1] || String(CFG.combat.default_attack_damage), 10);
  const size = CFG.dice.die_size || 20;
  const A = rollSide(atk.ref, size);
  const D = rollSide(def.ref, size);

  const aName = m[1].replace(/\s*\[ID:\d+\]/,'').trim();
  const dName = m[2].replace(/\s*\[ID:\d+\]/,'').trim();

  if (A.total <= D.total) {
    cron.push(`"${aName}" attacks "${dName}" — rolls ${A.die}×${A.power} (${A.total}) vs ${D.die}×${D.power} (${D.total}) — BLOCKED / evaded.`);
    return true;
  }
  // Hit — quality from ratio
  const ratio = A.total / Math.max(1, D.total);
  const hq = CFG.combat.hit_quality;
  let qual, mult;
  if (ratio < hq.glancing_below_ratio) { qual = 'glancing'; mult = hq.glancing_damage_mult; }
  else if (ratio < hq.solid_below_ratio) { qual = 'solid'; mult = hq.solid_damage_mult; }
  else { qual = 'CRITICAL'; mult = hq.critical_damage_mult; }
  const dmg = Math.round(dmgTag * mult);

  cron.push(`"${aName}" hits "${dName}" — ${A.total} vs ${D.total} (${qual}) for ${dmg} damage.`);

  if (def.isEnemy) {
    damageEnemy(game, def.ref, dmg, cron);
  } else {
    def.ref.hp = Math.max(0, (def.ref.hp ?? 0) - dmg);
    cron.push(`Character "${dName}" remaining HP ${def.ref.hp}/${def.ref.hp_max}.`);
    checkHpThresholds(game, dName, def.ref, def.type, nextId, cron);
  }
  return true;
}

// Optional scoping: parse "[A, B] vs [C, D]" from a Clash line.
// Fail-safe: any name that doesn't match is skipped; if a whole group matches
// nobody, that side falls back to "everyone present". Parsing can only narrow,
// never break — there is always a valid fight.
function scopeClashSide(fullList, bracketContent, nameOf) {
  if (!bracketContent) return fullList; // no scope given → all
  const wanted = bracketContent.split(',').map(s => s.replace(/\s*\[ID:\d+\]/, '').trim().toLowerCase()).filter(Boolean);
  if (!wanted.length) return fullList;
  const filtered = fullList.filter(item => {
    const nm = nameOf(item).toLowerCase();
    return wanted.some(w => nm === w);
  });
  return filtered.length ? filtered : fullList; // empty match → safe fallback to all
}

// Group Clash — abstract resolution for large fights (auto-used when a side is big).
function processClash(game, txt, cron) {
  let allies = allChars(game).filter(x => (x.ref.hp ?? 1) > 0);
  let enemies = ensureCombat(game).enemies.filter(e => e.alive !== false);
  if (!allies.length || !enemies.length) { cron.push(`Clash ignored — need living combatants on both sides.`); return true; }

  // Optional "[allies] vs [enemies]" scoping. Brackets are split around "vs".
  const vsIdx = txt.search(/\bvs\b/i);
  const before = vsIdx >= 0 ? txt.slice(0, vsIdx) : txt;
  const after  = vsIdx >= 0 ? txt.slice(vsIdx) : '';
  const allyBracket  = (before.match(/\[([^\]]+)\]/) || [])[1];
  const enemyBracket = (after.match(/\[([^\]]+)\]/)  || [])[1];
  allies  = scopeClashSide(allies,  allyBracket,  a => a.ref.name || '');
  enemies = scopeClashSide(enemies, enemyBracket, e => e.name || '');

  const sideStrength = (members, getCount) =>
    members.reduce((s, m) => s + (5 + combatMod(m.ref || m)) * charPower(m.ref || m) * (getCount ? (m.count || 1) : 1), 0);

  const Sa = sideStrength(allies, false);
  const Se = enemies.reduce((s, e) => s + (5 + combatMod(e)) * charPower(e) * (e.count || 1), 0);
  const size = CFG.dice.die_size || 20;
  const ra = rollDie(size), re = rollDie(size);
  const effA = Sa * ra, effE = Se * re;
  const alliesWin = effA >= effE;
  const ratio = Math.max(effA, effE) / Math.max(1, Math.min(effA, effE));

  let severity = ratio >= 3 ? 'rout' : ratio >= 1.5 ? 'decisive' : 'grinding';
  cron.push(`CLASH — Allies ${effA} (str ${Sa}×roll ${ra}) vs Enemies ${effE} (str ${Se}×roll ${re}). ${alliesWin ? 'Allies' : 'Enemies'} win — ${severity}.`);

  // Apply consequences
  const losers = alliesWin ? 'enemies' : 'allies';
  if (alliesWin) {
    // Reduce enemy numbers/hp by severity
    const kill = severity === 'rout' ? 0.6 : severity === 'decisive' ? 0.35 : 0.15;
    enemies.forEach(e => {
      if (e.count > 1) { const dead = Math.max(1, Math.round(e.count * kill)); e.count -= dead; if (e.count <= 0) e.alive = false; cron.push(`${dead} "${e.name}" cut down (${Math.max(0,e.count)} left).`); }
      else { const d = Math.round(e.hp_max * (kill + 0.2)); damageEnemy(game, e, d, cron); }
    });
    // Allies take light damage on grinding/decisive
    if (severity !== 'rout') {
      const dmg = severity === 'decisive' ? 0.12 : 0.2;
      allies.forEach(a => { const dd = Math.round((a.ref.hp_max||100)*dmg*Math.random()); if (dd>0){ a.ref.hp = Math.max(0,(a.ref.hp||0)-dd); cron.push(`Character "${a.ref.name}" takes ${dd} in the melee (${a.ref.hp}/${a.ref.hp_max}).`);} });
    }
  } else {
    // Allies lose — distribute heavy damage; possible downing
    const frac = severity === 'rout' ? 0.5 : severity === 'decisive' ? 0.33 : 0.18;
    allies.forEach(a => {
      const dd = Math.round((a.ref.hp_max||100) * frac * (0.6 + Math.random()*0.8));
      a.ref.hp = Math.max(0, (a.ref.hp||0) - dd);
      cron.push(`Character "${a.ref.name}" takes ${dd} damage (${a.ref.hp}/${a.ref.hp_max}).`);
    });
  }
  cron.push(`GM DIRECTIVE: narrate the clash outcome (${alliesWin ? 'allied' : 'enemy'} ${severity} victory). Check the HP lines above for who is hurt.`);
  return true;
}

// ── DEATH ─────────────────────────────────────────────────────
function applyDeath(game, name, c, type, nextId, cron) {
  if (type === 'player') {
    cron.push(`Character "${name}" has died. Rewinding to last checkpoint…`);
    doRewind(game, name, cron);
  } else {
    c.hp = 0;
    c.status = 'Dead';
    if (type === 'guide') game.guide.alive = false;
    cron.push(`Character "${name}" has died.`);
  }
}

// ── CHECKPOINT + REWIND ───────────────────────────────────────
function doCheckpoint(game, name, eventId, cron) {
  // Heal everyone, restore MP/stamina, revive dead, clear non-permanent status effects
  allChars(game, true /* includeDead */).forEach(({ ref }) => {
    if (ref.hp_max != null) ref.hp = ref.hp_max;
    if (ref.mp_max != null) ref.mp = ref.mp_max;
    if (ref.stamina_max != null) ref.stamina = ref.stamina_max;
    if (ref.alive != null) ref.alive = true;
    if (ref.status === 'Dead') ref.status = 'Active';
    ref.status_effects = (ref.status_effects || []).filter(s => typeof s === 'object' && s.permanent);
  });
  game.character.fear_meter = 0;
  game.character.fear_level = 'Calm';

  // Snapshot
  game.watcher = game.watcher || {};
  game.watcher.checkpoint_event_id = eventId;
  writeJson(P.checkpoint, game);
  const chat = readJsonSafe(P.chat);
  if (chat) writeJson(P.chkChat, chat);

  cron.push(`Checkpoint saved at God's Domain (event #${eventId}). All injuries healed, temporary status effects cleared.`);
}

function doRewind(game, playerName, cron) {
  const snap = readJsonSafe(P.checkpoint);
  if (!snap) { cron.push(`No checkpoint found — cannot rewind.`); return; }

  const deaths = (game.deaths || 0) + 1;
  const chkId = snap.watcher?.checkpoint_event_id || 0;

  // Restore chat
  const chkChat = readJsonSafe(P.chkChat);
  if (chkChat) writeJson(P.chat, chkChat);

  // Truncate event log to checkpoint, THEN append the restoration note
  truncateEventLogTo(chkId);
  const lines = readEventLines();
  const nid = maxEventId(lines) + 1;
  appendCron(`Character "${playerName}" restored to last checkpoint. All events and changes after #${chkId} undone. Deaths total: ${deaths}.`, nid);

  // Restore game state
  snap.deaths = deaths;
  snap.watcher = snap.watcher || {};
  snap.watcher.last_processed_event_id = nid;
  snap.watcher.checkpoint_event_id = chkId;
  Object.keys(game).forEach(k => delete game[k]);
  Object.assign(game, snap);

  log(`REWIND: restored to checkpoint #${chkId}, deaths=${deaths}`);
}

// ── EVENT PROCESSING ──────────────────────────────────────────
// Returns array of cron message strings produced.
function processEvent(game, line, nextId) {
  const cron = [];
  const txt = line.text;

  // Character name (first quoted token after "Character")
  const nameM = txt.match(/Character\s+"([^"]+)"/i);
  const name = nameM ? nameM[1] : null;
  const chref = name ? resolveChar(game, name) : null;
  const c = chref ? chref.ref : null;

  // ---- God's Domain checkpoint ----
  if (/enters?\s+God'?s\s+Domain|enters?\s+God'?s\s+Space|returns?\s+to\s+(the\s+)?lobby/i.test(txt)) {
    doCheckpoint(game, name, line.id || 0, cron);
    return cron;
  }

  // ---- COMBAT: enemy registration ----
  if (/Enemy\s+"[^"]+"\s+appears/i.test(txt)) { registerEnemy(game, txt, cron); return cron; }

  // ---- COMBAT: enemy death ----
  if (/Enemy\s+"[^"]+"\s+has\s+died|Enemy\s+"[^"]+"\s+(?:is\s+)?killed/i.test(txt)) {
    const em = txt.match(/Enemy\s+"([^"]+)"/i);
    const e = em ? findEnemy(game, em[1]) : null;
    if (e) { e.alive = false; e.hp = 0; cron.push(`Enemy "${e.name}[ID:${e.id}]" has died.`); }
    return cron;
  }

  // ---- COMBAT: group clash ----
  if (/^Clash\b/i.test(txt)) { processClash(game, txt, cron); return cron; }

  // ---- COMBAT: opposed attack ----  (X attacks Y — X/Y can be character or Enemy)
  if (/"[^"]+"\s+attacks\s+"[^"]+"/i.test(txt)) { processAttack(game, txt, nextId, cron); return cron; }

  // ---- Death ----
  // ONLY the protagonist's death rewinds the game. Any other character
  // (guide, teammate, NPC) just dies — the story continues shorthanded.
  if (/has died/i.test(txt)) {
    if (!chref) return cron;
    if (chref.type === 'player') {
      doRewind(game, name, cron);
    } else {
      c.hp = 0;
      c.status = 'Dead';
      if (chref.type === 'guide') game.guide.alive = false;
      if (chref.type === 'npc') c.alive = false;
      cron.push(`Character "${name}" has died. The team continues without them.`);
    }
    return cron;
  }

  // ---- Dice roll ----
  if (/tries to|attempts|Difficulty/i.test(txt) && /Difficulty/i.test(txt)) {
    processRoll(game, name, txt, nextId, cron);
    return cron;
  }

  if (!c) return cron; // remaining events all need a character

  // ---- HP ----
  let m;
  if ((m = txt.match(/(?:loses?|looses?)\s+(\d+)\s*(?:HP|health)\b(?!.*max)/i))) {
    c.hp = Math.max(0, (c.hp ?? 0) - parseInt(m[1], 10));
    cron.push(`Character "${name}" remaining HP ${c.hp}/${c.hp_max}.`);
    checkHpThresholds(game, name, c, chref.type, nextId, cron);
  }
  else if ((m = txt.match(/gains?\s+(\d+)\s*(?:HP|health)\b(?!.*max)/i)) && !/maxhp|max hp|maximum/i.test(txt)) {
    c.hp = Math.min(c.hp_max ?? 9999, (c.hp ?? 0) + parseInt(m[1], 10));
    cron.push(`Character "${name}" HP restored to ${c.hp}/${c.hp_max}.`);
    checkHpThresholds(game, name, c, chref.type, nextId, cron);
  }
  else if ((m = txt.match(/gains?\s+(\d+)\s*max\s*hp\s+permanently/i))) {
    const amt = parseInt(m[1], 10);
    c.hp_max = (c.hp_max ?? 100) + amt; c.hp = (c.hp ?? 0) + amt;
    cron.push(`Character "${name}" max HP increased to ${c.hp_max}.`);
  }
  else if ((m = txt.match(/loses?\s+(\d+)\s*max\s*hp\s+permanently/i))) {
    const amt = parseInt(m[1], 10);
    c.hp_max = Math.max(1, (c.hp_max ?? 100) - amt); c.hp = Math.min(c.hp, c.hp_max);
    cron.push(`Character "${name}" max HP reduced to ${c.hp_max}.`);
  }
  // ---- XP ----
  else if ((m = txt.match(/gains?\s+(\d+)\s*XP/i))) {
    c.xp = (c.xp ?? 0) + parseInt(m[1], 10);
    cron.push(`Character "${name}" now has ${c.xp} XP.`);
    checkLevelUp(game, name, c, cron);
  }
  // ---- Points ----
  else if ((m = txt.match(/gains?\s+(\d+)\s*points?/i))) {
    game.points = (game.points ?? 0) + parseInt(m[1], 10);
    cron.push(`Team points: ${game.points}.`);
  }
  else if ((m = txt.match(/loses?\s+(\d+)\s*points?/i))) {
    game.points = Math.max(0, (game.points ?? 0) - parseInt(m[1], 10));
    cron.push(`Team points: ${game.points}.`);
  }
  // ---- Stats ----
  else if ((m = txt.match(/(gains?|loses?)\s+(\d+)\s+(STR|AGI|END|INT|LUCK|PSY|strength|agility|endurance|intelligence|luck|psyche)/i))) {
    const dir = /gain/i.test(m[1]) ? 1 : -1;
    const amt = parseInt(m[2], 10) * dir;
    const map = { str:'strength', agi:'agility', end:'endurance', int:'intelligence', luck:'luck', psy:'psyche_force', psyche:'psyche_force',
                  strength:'strength', agility:'agility', endurance:'endurance', intelligence:'intelligence' };
    const key = map[m[3].toLowerCase()] || m[3].toLowerCase();
    c[key] = Math.max(0, (c[key] ?? 0) + amt);
    const perm = /permanent/i.test(txt) ? ' (permanent)' : '';
    cron.push(`Character "${name}" ${key} is now ${c[key]}${perm}.`);
  }
  // ---- MP ----
  else if ((m = txt.match(/(?:loses?|looses?)\s+(\d+)\s*MP\b(?!.*max)/i))) {
    c.mp = Math.max(0, (c.mp ?? 0) - parseInt(m[1], 10));
    cron.push(`Character "${name}" remaining MP ${c.mp}/${c.mp_max}.`);
  }
  else if ((m = txt.match(/gains?\s+(\d+)\s*MP\b(?!.*max)/i)) && !/maxmp|max mp/i.test(txt)) {
    c.mp = Math.min(c.mp_max ?? 999, (c.mp ?? 0) + parseInt(m[1], 10));
    cron.push(`Character "${name}" MP restored to ${c.mp}/${c.mp_max}.`);
  }
  else if ((m = txt.match(/gains?\s+(\d+)\s*max\s*mp\s+permanently/i))) {
    const amt = parseInt(m[1], 10);
    c.mp_max = (c.mp_max ?? 0) + amt; c.mp = (c.mp ?? 0) + amt;
    cron.push(`Character "${name}" max MP increased to ${c.mp_max}.`);
  }
  // ---- Stamina ----
  else if ((m = txt.match(/(?:loses?|looses?)\s+(\d+)\s*(?:stamina|STA)\b(?!.*max)/i))) {
    c.stamina = Math.max(0, (c.stamina ?? 0) - parseInt(m[1], 10));
    cron.push(`Character "${name}" remaining stamina ${c.stamina}/${c.stamina_max}.`);
  }
  else if ((m = txt.match(/gains?\s+(\d+)\s*(?:stamina|STA)\b(?!.*max)/i))) {
    c.stamina = Math.min(c.stamina_max ?? 999, (c.stamina ?? 0) + parseInt(m[1], 10));
    cron.push(`Character "${name}" stamina restored to ${c.stamina}/${c.stamina_max}.`);
  }
  else if ((m = txt.match(/gains?\s+(\d+)\s*max\s*stamina\s+permanently/i))) {
    const amt = parseInt(m[1], 10);
    c.stamina_max = (c.stamina_max ?? 100) + amt; c.stamina = (c.stamina ?? 0) + amt;
    cron.push(`Character "${name}" max stamina increased to ${c.stamina_max}.`);
  }
  // ---- Fear meter ----
  else if ((m = txt.match(/gains?\s+(\d+)\s+fear\b/i))) {
    c.fear_meter = Math.min(100, (c.fear_meter ?? 0) + parseInt(m[1], 10));
    const fl = fearLevelFor(c.fear_meter);
    c.fear_level = fl.name;
    cron.push(`Character "${name}" fear +${parseInt(m[1],10)} (now ${c.fear_meter}/100 — ${fl.name}).`);
  }
  else if ((m = txt.match(/loses?\s+(\d+)\s+fear\b/i))) {
    c.fear_meter = Math.max(0, (c.fear_meter ?? 0) - parseInt(m[1], 10));
    const fl = fearLevelFor(c.fear_meter);
    c.fear_level = fl.name;
    cron.push(`Character "${name}" fear -${parseInt(m[1],10)} (now ${c.fear_meter}/100 — ${fl.name}).`);
  }
  else if ((m = txt.match(/fear\s*=\s*(\d+)/i))) {
    c.fear_meter = Math.max(0, Math.min(100, parseInt(m[1], 10)));
    const fl = fearLevelFor(c.fear_meter);
    c.fear_level = fl.name;
    cron.push(`Character "${name}" fear set to ${c.fear_meter}/100 — ${fl.name}.`);
  }
  // ---- Status effects ----
  else if ((m = txt.match(/gets?\s+(temporary|permanent)\s+status\s+effect\s+"([^"]+)"/i))) {
    addStatus(c, m[2], { permanent: /permanent/i.test(m[1]), negative: true });
    cron.push(`Character "${name}" gains ${m[1].toLowerCase()} status "${m[2]}".`);
  }
  else if ((m = txt.match(/(?:loses?|removes?)\s+status\s+effect\s+"([^"]+)"/i))) {
    removeStatus(c, m[1]);
    cron.push(`Character "${name}" loses status "${m[1]}".`);
  }
  // ---- Items ----
  else if ((m = txt.match(/gains?\s+item\s+"([^"]+?)(?:\[ID:(\d+)\])?"/i))) {
    c.items = c.items || [];
    c.items.push({ name: m[1].trim(), id: m[2] ? parseInt(m[2],10) : null, status: [] });
    cron.push(`Character "${name}" obtained "${m[1].trim()}".`);
  }
  else if ((m = txt.match(/(?:loses?|drops?|uses?)\s+item\s+"([^"]+?)(?:\[ID:(\d+)\])?"/i))) {
    const id = m[2] ? parseInt(m[2],10) : null;
    c.items = (c.items || []).filter(it =>
      id != null ? it.id !== id : (it.name || '').toLowerCase() !== m[1].trim().toLowerCase());
    cron.push(`Character "${name}" no longer has "${m[1].trim()}".`);
  }
  return cron;
}

// ---- Item status (no character) ----
function processItemStatus(game, txt, cron) {
  const m = txt.match(/Item\s+"([^"]+?)(?:\[ID:(\d+)\])?"\s+(?:has\s+)?gain(?:s|ed)?\s+status\s+"([^"]+)"/i);
  if (!m) return false;
  const id = m[2] ? parseInt(m[2],10) : null;
  let found = false;
  allChars(game, true).forEach(({ ref }) => {
    (ref.items || []).concat(ref.weapons || []).forEach(it => {
      if ((id != null && it.id === id) || (it.name || '').toLowerCase() === m[1].trim().toLowerCase()) {
        it.status = it.status || []; if (!it.status.includes(m[3])) it.status.push(m[3]); found = true;
      }
    });
  });
  if (found) cron.push(`Item "${m[1].trim()}" now has status "${m[3]}".`);
  return found;
}

// ── DERIVED CHECKS ────────────────────────────────────────────
function checkHpThresholds(game, name, c, type, nextId, cron) {
  if (c.hp <= 0) { applyDeath(game, name, c, type, nextId, cron); return; }
  const pct = (c.hp / (c.hp_max || 100)) * 100;
  const mw = CFG.auto_status.mortally_wounded;
  if (mw && pct < mw.trigger_hp_pct_below && !hasStatus(c, mw.status)) {
    addStatus(c, mw.status, { negative: true });
    cron.push(`Character "${name}" gains status "${mw.status}".`);
  } else if (mw && pct >= (mw.remove_when_above_pct ?? 30) && hasStatus(c, mw.status)) {
    removeStatus(c, mw.status);
    cron.push(`Character "${name}" recovers from "${mw.status}".`);
  }
}

function checkLevelUp(game, name, c, cron) {
  if (c.xp == null) return;
  const newLevel = levelForXp(c.xp);
  const oldLevel = c.level ?? 1;
  if (newLevel > oldLevel) {
    c.level = newLevel;
    const bonus = LEVEL_UP_HP_BONUS * (newLevel - oldLevel);
    if (c.hp_max != null) { c.hp_max += bonus; c.hp = (c.hp ?? 0) + bonus; }
    cron.push(`Character "${name}" has leveled up from lvl ${oldLevel} to lvl ${newLevel}. Max HP +${bonus}.`);
    cron.push(`GM DIRECTIVE: "${name}" reached level ${newLevel} — narrate a sense of growth and offer a fitting perk choice.`);
  }
}

// ── MAIN TICK ─────────────────────────────────────────────────
let dispatching = false;
let lastDispatchedMsgId = -1;
let gmSessionStarted = false;

function tick() {
  const game = readJsonSafe(P.game);
  if (!game) return; // mid-write or missing

  game.watcher = game.watcher || { last_processed_event_id: 0, checkpoint_event_id: 0 };
  game.watcher.running = true;
  game.watcher.last_tick = new Date().toISOString();

  const lines = readEventLines();
  let nextId = maxEventId(lines) + 1;
  const lastProcessed = game.watcher.last_processed_event_id || 0;

  const toProcess = lines.filter(l => l.source === 'system' && l.id != null && l.id > lastProcessed)
                         .sort((a, b) => a.id - b.id);

  let mutated = false;
  const cronBuffer = [];

  for (const line of toProcess) {
    let produced;
    if (/^Item\s+"/i.test(line.text)) { const buf = []; processItemStatus(game, line.text, buf); produced = buf; }
    else produced = processEvent(game, line, nextId);
    if (produced && produced.length) cronBuffer.push(...produced);
    mutated = true;
  }

  // Sync derived display fields
  if (game.character) {
    game.character.level = game.character.level ?? levelForXp(game.character.xp || 0);
    const fl = fearLevelFor(game.character.fear_meter || 0);
    game.character.fear_level = fl.name;
  }

  // Append cron outputs with fresh IDs
  if (cronBuffer.length) {
    const liveMax = maxEventId(readEventLines());
    let id = liveMax + 1;
    for (const text of cronBuffer) { appendCron(text, id); id++; }
    nextId = id;
  }

  // Advance cursor to the new max id in the file
  game.watcher.last_processed_event_id = maxEventId(readEventLines());
  if (mutated || cronBuffer.length || true) writeJson(P.game, game);

  // Chat dispatch (auto-GM)
  if (CFG.settings.auto_gm) maybeDispatchGM(game);
}

// ── AUTO-GM via Claude CLI ────────────────────────────────────
function maybeDispatchGM(game) {
  if (dispatching) return;
  const chat = readJsonSafe(P.chat);
  if (!chat || !Array.isArray(chat.messages) || !chat.messages.length) return;

  const last = chat.messages[chat.messages.length - 1];
  if (chat.status !== 'waiting_for_gm') return;
  if (last.sender !== 'player') return;          // only player messages trigger the GM
  if (last.id === lastDispatchedMsgId) return;    // already handled

  lastDispatchedMsgId = last.id;
  dispatchGM(last);
}

function dispatchGM(playerMsg) {
  dispatching = true;
  const useContinue = gmSessionStarted;
  const tool = CFG.settings.ai_tool || 'claude';

  log(`AUTO-GM: dispatching player message #${playerMsg.id} to ${tool}${useContinue ? ' (--continue)' : ' (new session)'}`);

  const prompt =
`[WATCHER EVENT] The player sent a new message. Act as the Terror Infinity Game Master.

Steps:
1. Read data/INDEX.md, system/gm-prompt.md, data/game.json, data/chat.json (latest messages), and the tail of data/event-log.txt.
2. Respond IN CHARACTER. Append your narration as a {"sender":"gm"} message to data/chat.json and set "status":"waiting_for_player".
3. Write EVERY mechanical consequence to data/event-log.txt as "System Message[ID:n]: ..." lines (continue numbering from the highest existing ID). Do NOT compute HP totals, XP, levels, or dice yourself — write the intent events; the watcher computes results.
4. For any uncertain action, write a roll-request event: System Message[ID:n]: Character "NAME" tries to ACTION. Difficulty N. (add [lethal] if failure means death).

Player message: ${JSON.stringify(playerMsg.content)}`;

  const promptFlag = tool === 'opencode' ? '--prompt' : '-p';
  const args = [promptFlag, prompt];
  let command;
  let extraArgs;

  if (tool === 'opencode') {
    command = CFG.settings.opencode_command || 'opencode';
    if (useContinue) args.push('--continue');
    extraArgs = CFG.settings.opencode_extra_args || [];
    if (CFG.settings.ai_model) { args.push('--model'); args.push(CFG.settings.ai_model); }
  } else {
    // claude (default)
    command = CFG.settings.claude_command || 'claude';
    if (useContinue) args.push('--continue');
    extraArgs = CFG.settings.claude_extra_args || [];
    if (CFG.settings.ai_model) { args.push('--model'); args.push(CFG.settings.ai_model); }
  }
  extraArgs.forEach(a => args.push(a));

  const child = spawn(command, args, {
    cwd: ROOT, shell: true, detached: true,
  });

  let out = '';
  child.stdout.on('data', d => { out += d; });
  child.stderr.on('data', d => { out += d; });

  child.on('close', code => {
    try { fs.appendFileSync(P.gmLog, `\n===== GM turn (msg #${playerMsg.id}, exit ${code}) ${new Date().toISOString()} =====\n${out}\n`); } catch (e) {}
    if (code === 0) { gmSessionStarted = true; log(`AUTO-GM: turn complete (msg #${playerMsg.id}).`); }
    else if (useContinue && !gmSessionStarted) {
      log(`AUTO-GM: --continue failed, retrying as new session.`);
      dispatching = false; gmSessionStarted = false; lastDispatchedMsgId = -1;
      return;
    } else {
      log(`AUTO-GM: ${command} exited ${code}. See gm.log.`);
    }
    dispatching = false;
  });

  child.on('error', err => {
    log(`AUTO-GM ERROR: ${err.message}. Is '${command}' installed and on PATH? Set settings.auto_gm=false to disable, or change ai_tool in config.`);
    dispatching = false;
  });
}

// ── BOOT ──────────────────────────────────────────────────────
function boot() {
  log('───────────────────────────────────────────────');
  log('Terror Infinity Watcher starting.');
  log(`Project: ${ROOT}`);
  const toolName = CFG.settings.ai_tool || 'claude';
  log(`Auto-GM: ${CFG.settings.auto_gm ? 'ON (' + toolName + ' CLI' + (CFG.settings.ai_model ? ' — ' + CFG.settings.ai_model : '') + ')' : 'OFF (run play terror-infinity manually)'}`);

  // Ensure files exist
  if (!fs.existsSync(P.eventLog)) fs.writeFileSync(P.eventLog, '');
  const game = readJsonSafe(P.game);
  if (game) { game.watcher = game.watcher || {}; game.watcher.running = true; writeJson(P.game, game); }

  const interval = CFG.settings.poll_interval_ms || 1500;
  setInterval(() => { try { tick(); } catch (e) { log('TICK ERROR: ' + e.message + '\n' + e.stack); } }, interval);
  log(`Watching every ${interval}ms. Press Ctrl+C to stop.`);
}

process.on('SIGINT', () => {
  const game = readJsonSafe(P.game);
  if (game && game.watcher) { game.watcher.running = false; writeJson(P.game, game); }
  log('Watcher stopped.');
  process.exit(0);
});

// --once : process a single tick and exit (for testing / harnesses).
if (process.argv.includes('--once')) {
  if (!fs.existsSync(P.eventLog)) fs.writeFileSync(P.eventLog, '');
  try { tick(); } catch (e) { console.error('TICK ERROR:', e.message); }
  process.exit(0);
} else {
  boot();
}
