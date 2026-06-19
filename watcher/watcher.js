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
  gmState:     path.join(ROOT, 'watcher', 'gm-state.json'),
  pidFile:     path.join(ROOT, 'watcher', 'watcher.pid'),
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
  // Retry rename up to 5x — Windows Defender/Search can briefly hold the lock
  for (let i = 0; i < 5; i++) {
    try { fs.renameSync(tmp, file); return; } catch (e) {
      if (i === 4) throw e;
      const until = Date.now() + 60; while (Date.now() < until) {} // ~60ms spin
    }
  }
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
  const p = (game.partners || []).find(x => (x.name || '').toLowerCase() === n);
  if (p) return { ref: p, type: 'partner' };
  return null;
}

function allChars(game, includeDead) {
  const out = [];
  if (game.character?.name) out.push({ ref: game.character, type: 'player' });
  if (game.guide?.name && (includeDead || game.guide.alive !== false)) out.push({ ref: game.guide, type: 'guide' });
  (game.team?.members || []).forEach(m => { if (includeDead || (m.hp ?? 1) > 0) out.push({ ref: m, type: 'member' }); });
  (game.npcs || []).forEach(n => { if (includeDead || n.alive !== false) out.push({ ref: n, type: 'npc' }); });
  (game.partners || []).forEach(p => { if (includeDead || p.alive !== false) out.push({ ref: p, type: 'partner' }); });
  return out;
}

// Resolve a location id to its human name (and sublocation) for the digest.
function locationLabel(game, id, sub) {
  if (!id) return 'unknown';
  const loc = (game.world_map?.locations || []).find(l => l.id === id);
  const base = loc ? loc.name : id;
  if (!sub) return base;
  const subObj = (loc?.sublocations || []).find(s => (typeof s === 'object' ? s.id : s) === sub);
  const subName = subObj ? (typeof subObj === 'object' ? subObj.name : subObj) : sub;
  return `${base} / ${subName}`;
}
function statusNames(c) {
  return (c.status_effects || []).map(s => (typeof s === 'string' ? s : s.name)).filter(Boolean);
}

// ── Stat / skill helpers ──────────────────────────────────────
function statValue(ch, statName) {
  const map = { str: 'strength', agi: 'agility', end: 'endurance', int: 'intelligence',
                luck: 'luck', psy: 'psyche_force', psyche: 'psyche_force',
                cha: 'charisma', charisma: 'charisma', app: 'appearance', appearance: 'appearance' };
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

// Luck die bonus — non-linear scaling so high luck feels like protagonist-level fate.
// Average human sits 5-15 (no bonus). At 50 the world bends toward them. At 100 barely anything kills them.
function luckDieBonus(luck) {
  const l = luck ?? 0;
  if (l <= 9)  return 0;
  if (l <= 19) return 1;
  if (l <= 29) return 2;
  if (l <= 39) return 4;
  if (l <= 49) return 6;
  if (l <= 59) return 8;
  if (l <= 69) return 11;
  if (l <= 79) return 14;
  if (l <= 89) return 17;
  if (l <= 99) return 19;
  return 20; // 100+ — minimum effective die 21, beats most realistic DCs
}

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
  // Luck scaling: non-linear bonus silently added to die before power (hidden from player)
  const luckBonus = luckDieBonus(c.luck);
  const final = (die + luckBonus + modifier) * power;

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

  // ── System Curse: luck 0 cascades near-misses to catastrophe ─
  if ((c.luck ?? 1) === 0 && tier === 'near miss') {
    tier = 'OVERWHELMING FAILURE';
    extra = 'negative';
    cron.push(`GM DIRECTIVE: System Curse active on "${name}" — near-miss cascades to OVERWHELMING FAILURE. Fate is not just absent, it is hostile.`);
  }

  // ── Luck delta ────────────────────────────────────────────────
  // nat20/nat1 SET the delta to exactly ±1 — they don't stack with borderline/near-miss.
  // Otherwise borderline (+1) and near miss (-1) set above stand as-is.
  if (nat20)     luckDelta = 1;
  else if (nat1) luckDelta = -1;

  // Apply luck change. Floor = 1 — luck 0 is System-only (see System Curse).
  if (luckDelta !== 0 && c.luck != null) {
    c.luck = Math.max(1, c.luck + luckDelta);
    cron.push(`Character "${name}" luck ${luckDelta > 0 ? '+' : ''}${luckDelta} (now ${c.luck}).`);
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

// ── SOCIAL / RELATIONSHIPS ────────────────────────────────────
// Affection is directional: c.relationships[OtherName] = { affection, status }.
function affectionBand(n) {
  const bands = (CFG.social && CFG.social.affection_bands) || [];
  for (const b of bands) if (n <= b.max) return b.label;
  return 'Neutral';
}
function getRel(c, otherName) {
  c.relationships = c.relationships || {};
  if (!c.relationships[otherName]) c.relationships[otherName] = { affection: 0, status: affectionBand(0) };
  return c.relationships[otherName];
}
function setAffection(c, otherName, value) {
  const rel = getRel(c, otherName);
  const lo = CFG.social?.affection_min ?? -100, hi = CFG.social?.affection_max ?? 100;
  rel.affection = Math.max(lo, Math.min(hi, Math.round(value)));
  rel.status = affectionBand(rel.affection);
  return rel;
}
function goodEvilAxis(alignment) {
  const a = (alignment || '').toLowerCase();
  if (a.includes('good')) return 'good';
  if (a.includes('evil')) return 'evil';
  return 'neutral';
}
function stripId(s) { return (s || '').replace(/\s*\[ID:\d+\]/, '').trim(); }

// ── ENCUMBRANCE / WEIGHT ──────────────────────────────────────
function itemWeight(it) { return (it && typeof it.weight === 'number') ? it.weight : 0; }
function onHandWeight(c) {
  let w = 0;
  for (const it of (c.items || []))   w += itemWeight(it);
  for (const it of (c.weapons || [])) w += itemWeight(it);
  return Math.round(w * 100) / 100;
}
function carryCapacity(c) { return (c.strength || 0) * (CFG.encumbrance?.carry_capacity_per_str_kg ?? 5); }
function maxLift(c)       { return (c.strength || 0) * (CFG.encumbrance?.max_lift_per_str_kg ?? 10); }
function updateEncumbrance(c, name, cron) {
  const cap = carryCapacity(c);
  const load = onHandWeight(c);
  const status = CFG.encumbrance?.encumbered_status || 'Encumbered';
  if (load > cap && cap > 0) {
    if (!hasStatus(c, status)) {
      addStatus(c, status, { permanent: false, negative: true });
      cron.push(`WATCHER NOTICE: "${name}" is over carry capacity (${load}kg / ${cap}kg) — now Encumbered. Movement and agility-based actions are slowed until they drop or store weight (a storage ring is weightless).`);
    }
  } else if (hasStatus(c, status)) {
    removeStatus(c, status);
    cron.push(`Character "${name}" is no longer encumbered (${load}kg / ${cap}kg).`);
  }
}

// ── COMMUNICATION MEANS ───────────────────────────────────────
function hasItemLike(c, re) {
  for (const pool of [c.items, c.weapons, c.equipped, c.storage])
    for (const it of (pool || [])) if (re.test((it.name || '').toLowerCase())) return true;
  return false;
}
function hasSkillLike(c, re) {
  return Object.keys(c.skills || {}).some(k => re.test(k.toLowerCase()));
}
function hasCommMeans(c, type) {
  const t = (type || '').toLowerCase();
  // Telepathic / psychic channels rely on a stat, skill, or soul-link item.
  if (/tele|psych|mind|soul|link/.test(t))
    return (c.psyche_force || 0) >= 5 || hasSkillLike(c, /psych|tele|mind/) || hasItemLike(c, /soul.?link|psyche|telepath|mind/);
  // Device channels rely on a matching item.
  return hasItemLike(c, /radio|comm|walkie|earpiece|transceiver|phone|intercom|headset|signal|transmitter|receiver/);
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

  const aName = stripId(m[1]);
  const dName = stripId(m[2]);

  // ── Watcher correction: character-vs-character sanity checks ──
  if (!atk.isEnemy && !def.isEnemy) {
    const Ac = atk.ref, Dc = def.ref;
    const ranged = /\[(?:ranged|long-?range|sniper|scoped|artillery)\]/i.test(txt);
    if ((Ac.location || null) !== (Dc.location || null) && !ranged) {
      cron.push(`WATCHER WARNING: "${aName}" cannot attack "${dName}" — they are in different locations (${Ac.location || '?'} vs ${Dc.location || '?'}). Only a declared long-range attack (tag the event [ranged]) reaches across locations. Attack NOT resolved — correct the scene.`);
      return true;
    }
    const rel = (Ac.relationships || {})[dName];
    const thr = CFG.social?.attack_despite_affection_threshold ?? 40;
    if (rel && rel.affection >= thr) {
      cron.push(`WATCHER NOTICE: "${aName}" is attacking "${dName}" despite a positive bond (affection ${rel.affection}, ${rel.status}). Allowed — but motivate it (mind control, betrayal, possession, a forced choice). Make turning on them land emotionally.`);
    }
  }

  const dmgTag = parseInt((txt.match(/\b(\d+)\s*(?:dmg|damage)\b/i) || [])[1] || String(CFG.combat.default_attack_damage), 10);
  const size = CFG.dice.die_size || 20;
  const A = rollSide(atk.ref, size);
  const D = rollSide(def.ref, size);

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

// ── SOCIAL EVENT HANDLERS ─────────────────────────────────────
// Face-to-face interaction between two characters. Validates co-location and
// reports the current relationship so the GM can play it accurately.
function processInteraction(game, txt, cron) {
  const m = txt.match(/"([^"]+?)"\s+(?:interacts?\s+with|talks?\s+(?:to|with)|speaks?\s+(?:to|with)|meets?\s+(?:with\s+)?|approaches?|confronts?)\s+"([^"]+?)"/i);
  if (!m) return;
  const aName = stripId(m[1]), bName = stripId(m[2]);
  const aRef = resolveChar(game, aName), bRef = resolveChar(game, bName);
  if (!aRef || !bRef) { cron.push(`Interaction note — unknown character ("${aName}" / "${bName}").`); return; }
  const A = aRef.ref, B = bRef.ref;

  if ((A.location || null) !== (B.location || null)) {
    cron.push(`WATCHER WARNING: "${aName}" cannot directly interact with "${bName}" — they are in different locations (${aName}: ${A.location || 'unknown'}, ${bName}: ${B.location || 'unknown'}). Move one of them first, or have them use a communication device ("… via radio").`);
    return;
  }
  if ((A.sublocation || null) !== (B.sublocation || null)) {
    cron.push(`WATCHER NOTICE: "${aName}" and "${bName}" share a location (${A.location}) but are in different rooms (${A.sublocation || 'main area'} vs ${B.sublocation || 'main area'}). Confirm they're actually close enough to interact face-to-face.`);
  }
  const rAB = getRel(A, bName), rBA = getRel(B, aName);
  cron.push(`Relationship — "${aName}" → "${bName}": affection ${rAB.affection} (${rAB.status}); "${bName}" → "${aName}": affection ${rBA.affection} (${rBA.status}). Voice this in how they treat each other.`);
}

// Remote communication via a device or psychic channel. Bypasses co-location,
// but each side must actually possess the means.
function processComm(game, txt, cron) {
  const m = txt.match(/"([^"]+?)"\s+(?:contacts?|communicates?\s+with|radios?|calls?|signals?|messages?|reaches?(?:\s+out\s+to)?)\s+"([^"]+?)"\s+via\s+"?([^".;]+?)"?\s*[;.]?\s*$/i);
  if (!m) return;
  const aName = stripId(m[1]), bName = stripId(m[2]), type = m[3].trim();
  const aRef = resolveChar(game, aName), bRef = resolveChar(game, bName);
  if (!aRef || !bRef) { cron.push(`Comm note — unknown character ("${aName}" / "${bName}").`); return; }
  const A = aRef.ref, B = bRef.ref;

  const missing = [];
  if (!hasCommMeans(A, type)) missing.push(aName);
  if (!hasCommMeans(B, type)) missing.push(bName);
  if (missing.length) {
    cron.push(`WATCHER WARNING: ${missing.map(n => `"${n}"`).join(' and ')} ${missing.length > 1 ? 'have' : 'has'} no working ${type} (no matching device or skill) to communicate this way. Give them the item/ability first, or correct the scene — the contact can't happen via ${type}.`);
    return;
  }
  cron.push(`"${aName}" reaches "${bName}" via ${type} — both are equipped for it.`);
  const rAB = getRel(A, bName), rBA = getRel(B, aName);
  cron.push(`Relationship — "${aName}" → "${bName}": ${rAB.affection} (${rAB.status}); "${bName}" → "${aName}": ${rBA.affection} (${rBA.status}).`);
}

// Affection change — mutual ("affection between A and B …") or directional
// ("A affection toward B …"). Supports +N / -N / = N.
function processAffection(game, txt, cron) {
  let m;
  if ((m = txt.match(/affection\s+between\s+"([^"]+?)"\s+and\s+"([^"]+?)"\s*(=)?\s*([+-]?\d+)/i))) {
    const aName = stripId(m[1]), bName = stripId(m[2]);
    const isSet = !!m[3], val = parseInt(m[4], 10);
    const aRef = resolveChar(game, aName), bRef = resolveChar(game, bName);
    if (!aRef || !bRef) { cron.push(`Affection note — unknown character ("${aName}" / "${bName}").`); return true; }
    applyAffection(aRef.ref, aName, bRef.ref, bName, isSet, val, cron);
    applyAffection(bRef.ref, bName, aRef.ref, aName, isSet, val, cron);
    return true;
  }
  if ((m = txt.match(/"([^"]+?)"\s+affection\s+(?:toward|towards|for)\s+"([^"]+?)"\s*(=)?\s*([+-]?\d+)/i))) {
    const aName = stripId(m[1]), bName = stripId(m[2]);
    const isSet = !!m[3], val = parseInt(m[4], 10);
    const aRef = resolveChar(game, aName), bRef = resolveChar(game, bName);
    if (!aRef) { cron.push(`Affection note — unknown character "${aName}".`); return true; }
    applyAffection(aRef.ref, aName, bRef?.ref || null, bName, isSet, val, cron);
    return true;
  }
  return false;
}

function applyAffection(A, aName, B, bName, isSet, val, cron) {
  const rel = getRel(A, bName);
  const before = rel.affection;
  setAffection(A, bName, isSet ? val : before + val);
  cron.push(`Affection — "${aName}" → "${bName}": ${before} → ${rel.affection} (${rel.status}).`);
  if (rel.affection > before && B) {
    const axA = goodEvilAxis(A.alignment), axB = goodEvilAxis(B.alignment);
    if ((axA === 'good' && axB === 'evil') || (axA === 'evil' && axB === 'good')) {
      cron.push(`WATCHER NOTICE: affection is rising between "${aName}" (${A.alignment || 'unaligned'}) and "${bName}" (${B.alignment || 'unaligned'}) — opposing good/evil alignments. Keep it realistic: a bond across that gap should be hard-won, tense, and genuinely motivated, not casual.`);
    }
  }
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
    if (type === 'npc' || type === 'partner') c.alive = false;
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

    // First-movie mercy rule: heal physical disabilities on first movie completion
    if ((game.movie_number || 1) <= 1 && ref.weaknesses && ref.weaknesses.length) {
      const healed = ref.weaknesses.filter(w => w.heals_on_movie_end);
      if (healed.length) {
        ref.weaknesses = ref.weaknesses.filter(w => !w.heals_on_movie_end);
        healed.forEach(w => cron.push(`Mercy heal: "${ref.name}" — physical disability "${w.name}" cleared by God's Space (first-movie reward).`));
      }
    }
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

  // ---- SOCIAL: remote communication ("A contacts B via radio") — check before interaction/affection ----
  if (/"[^"]+"\s+(?:contacts?|communicates?\s+with|radios?|calls?|signals?|messages?|reaches?(?:\s+out\s+to)?)\s+"[^"]+"\s+via\s+/i.test(txt)) {
    processComm(game, txt, cron); return cron;
  }
  // ---- SOCIAL: affection change ----
  if (/affection/i.test(txt)) {
    if (processAffection(game, txt, cron)) return cron;
  }
  // ---- SOCIAL: face-to-face interaction ----
  if (/"[^"]+"\s+(?:interacts?\s+with|talks?\s+(?:to|with)|speaks?\s+(?:to|with)|meets?\s+(?:with\s+)?|approaches?|confronts?)\s+"[^"]+"/i.test(txt) && !/\bvia\b/i.test(txt)) {
    processInteraction(game, txt, cron); return cron;
  }

  // ---- TIMERS / COUNTDOWNS (turn-based; decremented once per GM turn) ----
  let tmrM;
  if ((tmrM = txt.match(/(?:start|set|begin)\s+(?:a\s+)?(?:countdown\s+)?timer\s+"([^"]+)"\s+(?:(?:at|for|to)\s+)?(\d+)\s*turns?/i))) {
    const tName = tmrM[1].trim(), turns = parseInt(tmrM[2], 10);
    game.timers = game.timers || [];
    const existing = game.timers.find(t => (t.name || '').toLowerCase() === tName.toLowerCase());
    if (existing) { existing.turns_left = turns; cron.push(`Countdown "${tName}" reset to ${turns} turn(s).`); }
    else { game.timers.push({ name: tName, turns_left: turns, started_turn: game.watcher?.turn ?? 0 }); cron.push(`Countdown "${tName}" started — ${turns} turn(s).`); }
    return cron;
  }
  if ((tmrM = txt.match(/(?:cancel|stop|clear|remove)\s+timer\s+"([^"]+)"/i))) {
    const tName = tmrM[1].trim();
    const before = (game.timers || []).length;
    game.timers = (game.timers || []).filter(t => (t.name || '').toLowerCase() !== tName.toLowerCase());
    cron.push(before > (game.timers || []).length ? `Countdown "${tName}" cancelled.` : `Cancel ignored — no countdown "${tName}".`);
    return cron;
  }

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
      if (chref.type === 'npc' || chref.type === 'partner') c.alive = false;
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
  // ---- Location / movement ----
  else if ((m = txt.match(/moves?\s+to\s+"([^"\/]+?)(?:\s*\/\s*([^"]+?))?"/i))) {
    const loc = m[1].trim();
    const sub = m[2] ? m[2].trim() : null;
    const prev = c.location;
    c.location = loc;
    if (sub) c.sublocation = sub; else delete c.sublocation;
    // Mark sublocation discovered in world_map
    if (sub && game.world_map && Array.isArray(game.world_map.locations)) {
      const parentLoc = game.world_map.locations.find(l => l.id === loc);
      if (parentLoc && Array.isArray(parentLoc.sublocations)) {
        const subObj = parentLoc.sublocations.find(s => typeof s === 'object' && s.id === sub);
        if (subObj) subObj.discovered = true;
      }
    }
    const where = sub ? `${loc} / ${sub}` : loc;
    cron.push(`Character "${name}" moved${prev && prev !== loc ? ` from ${prev}` : ''} to ${where}.`);
  }
  // ---- Stats ----
  else if ((m = txt.match(/(gains?|loses?)\s+(\d+)\s+(STR|AGI|END|INT|LUCK|PSY|CHA|APP|strength|agility|endurance|intelligence|luck|psyche|charisma|appearance)/i))) {
    const dir = /gain/i.test(m[1]) ? 1 : -1;
    const amt = parseInt(m[2], 10) * dir;
    const map = { str:'strength', agi:'agility', end:'endurance', int:'intelligence', luck:'luck', psy:'psyche_force', psyche:'psyche_force',
                  cha:'charisma', app:'appearance',
                  strength:'strength', agility:'agility', endurance:'endurance', intelligence:'intelligence',
                  charisma:'charisma', appearance:'appearance' };
    const key = map[m[3].toLowerCase()] || m[3].toLowerCase();
    c[key] = Math.max(0, (c[key] ?? 0) + amt);
    const perm = /permanent/i.test(txt) ? ' (permanent)' : '';
    cron.push(`Character "${name}" ${key} is now ${c[key]}${perm}.`);
  }
  // ---- Alignment ----
  else if ((m = txt.match(/alignment\s+(?:shifts?\s+to|becomes?|is\s+now|changes?\s+to)\s+"?(Lawful Good|Neutral Good|Chaotic Good|Lawful Neutral|True Neutral|Neutral|Chaotic Neutral|Lawful Evil|Neutral Evil|Chaotic Evil)"?/i))
            || (m = txt.match(/becomes?\s+"(Lawful Good|Neutral Good|Chaotic Good|Lawful Neutral|True Neutral|Chaotic Neutral|Lawful Evil|Neutral Evil|Chaotic Evil)"/i))) {
    let al = m[1].replace(/\b\w/g, ch => ch.toUpperCase());
    if (al.toLowerCase() === 'neutral') al = 'True Neutral';
    const prev = c.alignment || 'unset';
    c.alignment = al;
    cron.push(`Character "${name}" alignment: ${prev} → ${al}.`);
  }
  // ---- Loyalty (team trust / betrayal meter, 0-100) ----
  else if ((m = txt.match(/loyalty\s*(?:([+\-])\s*(\d+)|=\s*(\d+))/i))) {
    const cur = c.loyalty ?? 50;
    let next;
    if (m[3] != null) next = parseInt(m[3], 10);
    else next = cur + (m[1] === '-' ? -1 : 1) * parseInt(m[2], 10);
    c.loyalty = Math.max(0, Math.min(100, next));
    cron.push(`Character "${name}" loyalty is now ${c.loyalty}/100.`);
    if (c.loyalty <= 15 && (chref.type === 'npc'))
      cron.push(`GM DIRECTIVE: "${name}" loyalty is critically low (${c.loyalty}) — they are on the verge of breaking from the team or betraying it. Let it show.`);
  }
  // ---- Partner: granted freedom (created being becomes a free participant) ----
  else if (/(?:is\s+)?granted\s+freedom|becomes?\s+free|buys?\s+(?:their|his|her)\s+freedom/i.test(txt) && chref.type === 'partner') {
    c.free = true;
    cron.push(`Partner "${name}" has been granted freedom — they are now a free participant with their own standing, no longer bound to their creator.`);
    cron.push(`GM DIRECTIVE: "${name}" is now free. They keep their bond to ${name === (game.character?.name) ? 'themselves' : 'their creator'} but choose it now rather than being compelled. They gain their own goals and may earn points/rewards as a true team member.`);
  }
  // ---- Genetic lock (shop or combat evolution) ----
  else if ((m = txt.match(/opens?\s+genetic\s+lock\s+(\d+)|undergoes?\s+combat\s+evolution/i))) {
    const lockN = m[1] ? parseInt(m[1], 10) : (c.genetic_locks_opened ?? 0) + 1;
    const current = c.genetic_locks_opened ?? 0;
    if (lockN !== current + 1) {
      cron.push(`WATCHER WARNING: Cannot open lock ${lockN} — character currently has ${current} locks open.`);
    } else {
      c.genetic_locks_opened = lockN;
      const LOCK_BONUSES = {
        1: { all:5, hp:50, rank:'F' },
        2: { strength:10, endurance:10, hp:100, rank:'E' },
        3: { intelligence:15, agility:10, psyche_force:30, rank:'D' },
        4: { all:25, hp:300, rank:'C' },
        5: { all:40, hp:500, rank:'B' },
      };
      const bonus = LOCK_BONUSES[lockN];
      if (bonus) {
        const ALL_STATS = ['strength','agility','endurance','intelligence','psyche_force'];
        const apply = bonus.all ? ALL_STATS.reduce((o,s)=>{o[s]=bonus.all;return o},{}) : {};
        Object.assign(apply, Object.fromEntries(Object.entries(bonus).filter(([k]) => ALL_STATS.includes(k))));
        for (const [stat, amt] of Object.entries(apply)) {
          c[stat] = (c[stat] ?? 0) + amt;
        }
        if (bonus.hp) { c.hp_max = (c.hp_max ?? 100) + bonus.hp; c.hp = (c.hp ?? 0) + bonus.hp; }
        c.rank = bonus.rank;
        const via = /combat evolution/i.test(txt) ? 'combat evolution (no cost)' : 'shop purchase';
        cron.push(`Character "${name}" opens genetic lock ${lockN} via ${via}. New rank: ${bonus.rank}.`);
        cron.push(`Stat gains: ${Object.entries(apply).map(([k,v])=>`${k} +${v}`).join(', ')}${bonus.hp?`, HP_max +${bonus.hp}`:''}. Current HP: ${c.hp}/${c.hp_max}.`);
        cron.push(`GM DIRECTIVE: Narrate the genetic lock opening for "${name}" — describe the physical sensation: something tearing free, a wave of heat, a moment of clarity. The world looks slightly different after. Make it visceral.`);
      }
    }
  }
  // ---- System Curse (luck = 0, System-only) ----
  else if ((m = txt.match(/receives?\s+System\s+Curse\s*[—–-]\s*(test|elimination)/i))) {
    const variant = m[1].toLowerCase();
    c.luck = 0;
    const note = variant === 'test'
      ? 'System Test — fate suspended until your limit. Will lift if you survive.'
      : 'System Elimination — fate inverted until dead or out of the movie.';
    addStatus(c, `System Curse (${variant})`, { permanent: false, negative: true, note });
    cron.push(`Character "${name}" luck set to 0. System Curse (${variant}) active.`);
    cron.push(`GM DIRECTIVE: The System has personally suspended "${name}"'s luck. Announce this with weight — not as flavour but as a declaration. The ${variant === 'test' ? 'test ends when they hit their genuine limit; the System will observe without mercy until then' : 'elimination curse does not lift — every near-miss cascades, every close call fails, until they die or leave the movie world'}. Near-misses at luck 0 become OVERWHELMING FAILURES. Play this as fate itself turning its full attention on them.`);
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
  else if ((m = txt.match(/gains?\s+item\s+"([^"]+?)(?:\[ID:(\d+)\])?"(?:[^\n]*?\bweigh(?:s|ing|t)?\s*(\d+(?:\.\d+)?)\s*(?:kg)?)?/i))) {
    const itemName = m[1].trim();
    const weight = m[3] != null ? parseFloat(m[3]) : 0;
    const lift = maxLift(c);
    if (weight > 0 && lift > 0 && weight > lift) {
      cron.push(`WATCHER WARNING: "${name}" cannot pick up "${itemName}" alone — it weighs ${weight}kg, beyond their lift limit (${lift}kg at STR ${c.strength}). Narrate them failing to carry it (drag it, get help, or leave it). Item NOT added.`);
    } else {
      c.items = c.items || [];
      c.items.push({ name: itemName, id: m[2] ? parseInt(m[2],10) : null, status: [], ...(weight > 0 ? { weight } : {}) });
      cron.push(`Character "${name}" obtained "${itemName}"${weight > 0 ? ` (${weight}kg)` : ''}.`);
      updateEncumbrance(c, name, cron);
    }
  }
  else if ((m = txt.match(/(?:loses?|drops?|uses?)\s+item\s+"([^"]+?)(?:\[ID:(\d+)\])?"/i))) {
    const id = m[2] ? parseInt(m[2],10) : null;
    c.items = (c.items || []).filter(it =>
      id != null ? it.id !== id : (it.name || '').toLowerCase() !== m[1].trim().toLowerCase());
    cron.push(`Character "${name}" no longer has "${m[1].trim()}".`);
    updateEncumbrance(c, name, cron);
  }
  // ---- Storage Ring: store / retrieve ----
  else if ((m = txt.match(/stores?\s+item\s+"([^"]+?)(?:\[ID:(\d+)\])?"/i))) {
    const itemName = m[1].trim();
    const id = m[2] ? parseInt(m[2],10) : null;
    const match = it => id != null ? it.id === id : (it.name||'').toLowerCase() === itemName.toLowerCase();
    let pool = (c.items || []).find(match) ? 'items' : ((c.weapons || []).find(match) ? 'weapons' : null);
    if (!pool) { cron.push(`Store ignored — "${itemName}" not on hand for ${name}.`); }
    else {
      const idx = c[pool].findIndex(match);
      const [item] = c[pool].splice(idx, 1);
      c.storage = c.storage || [];
      item._from = pool;
      c.storage.push(item);
      cron.push(`Character "${name}" stored "${itemName}" in the ring.`);
      updateEncumbrance(c, name, cron);
    }
  }
  else if ((m = txt.match(/retrieves?\s+item\s+"([^"]+?)(?:\[ID:(\d+)\])?"/i))) {
    const itemName = m[1].trim();
    const id = m[2] ? parseInt(m[2],10) : null;
    const match = it => id != null ? it.id === id : (it.name||'').toLowerCase() === itemName.toLowerCase();
    c.storage = c.storage || [];
    const idx = c.storage.findIndex(match);
    if (idx === -1) { cron.push(`Retrieve ignored — "${itemName}" not in ${name}'s ring.`); }
    else {
      const [item] = c.storage.splice(idx, 1);
      const pool = item._from === 'weapons' ? 'weapons' : 'items';
      delete item._from;
      c[pool] = c[pool] || [];
      c[pool].push(item);
      cron.push(`Character "${name}" retrieved "${itemName}" from the ring.`);
      updateEncumbrance(c, name, cron);
    }
  }
  // ---- Equip / unequip ----
  else if ((m = txt.match(/equips?\s+"([^"]+?)(?:\[ID:(\d+)\])?"/i))) {
    const itemName = m[1].trim();
    const itemId   = m[2] ? parseInt(m[2],10) : null;
    c.items    = c.items    || [];
    c.equipped = c.equipped || [];
    const item = c.items.find(it => itemId != null ? it.id === itemId : (it.name||'').toLowerCase() === itemName.toLowerCase())
              || c.weapons?.find(it => itemId != null ? it.id === itemId : (it.name||'').toLowerCase() === itemName.toLowerCase());
    if (!item) {
      cron.push(`Equip ignored — "${itemName}" not found in ${name}'s inventory.`);
    } else {
      const slot = item.slot || 'misc';
      const isRing = /ring/i.test(itemName) || /ring/i.test(slot);
      const alreadyEquipped = c.equipped.find(e => (e.id != null && e.id === item.id) || e.name === item.name);
      const slotOccupied = !isRing && c.equipped.find(e => e.slot === slot && slot !== 'misc');
      if (alreadyEquipped) {
        cron.push(`Equip ignored — "${itemName}" is already equipped.`);
      } else if (slotOccupied) {
        cron.push(`Equip ignored — slot "${slot}" already occupied by "${slotOccupied.name}". Unequip it first.`);
      } else {
        c.equipped.push({ name: item.name, id: item.id ?? null, slot });
        // Apply stat bonuses
        if (item.stat_bonuses) {
          for (const [stat, val] of Object.entries(item.stat_bonuses)) {
            if (typeof c[stat] === 'number') c[stat] += val;
            else c[stat] = val;
          }
          const bonusList = Object.entries(item.stat_bonuses).map(([s,v])=>`${s} ${v>0?'+':''}${v}`).join(', ');
          cron.push(`Character "${name}" equipped "${itemName}" (${bonusList}).`);
        } else {
          cron.push(`Character "${name}" equipped "${itemName}".`);
        }
      }
    }
  }
  else if ((m = txt.match(/unequips?\s+"([^"]+?)(?:\[ID:(\d+)\])?"/i))) {
    const itemName = m[1].trim();
    const itemId   = m[2] ? parseInt(m[2],10) : null;
    c.equipped = c.equipped || [];
    const idx = c.equipped.findIndex(e => itemId != null ? e.id === itemId : e.name.toLowerCase() === itemName.toLowerCase());
    if (idx === -1) {
      cron.push(`Unequip ignored — "${itemName}" is not equipped by ${name}.`);
    } else {
      const entry = c.equipped[idx];
      c.equipped.splice(idx, 1);
      // Remove stat bonuses: look up item to get bonuses
      const item = (c.items || []).find(it => entry.id != null ? it.id === entry.id : it.name === entry.name)
                || (c.weapons || []).find(it => entry.id != null ? it.id === entry.id : it.name === entry.name);
      if (item?.stat_bonuses) {
        for (const [stat, val] of Object.entries(item.stat_bonuses)) {
          if (typeof c[stat] === 'number') c[stat] -= val;
        }
        const bonusList = Object.entries(item.stat_bonuses).map(([s,v])=>`${s} ${v>0?'+':''}${v}`).join(', ');
        cron.push(`Character "${name}" unequipped "${itemName}" (${bonusList} removed).`);
      } else {
        cron.push(`Character "${name}" unequipped "${itemName}".`);
      }
    }
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

// ── GROUND-TRUTH DIGEST ───────────────────────────────────────
// A compact, authoritative snapshot injected into every GM turn so the GM
// narrates from current state instead of decayed context. This is the primary
// defense against confabulation: numbers it would otherwise "remember" wrong.
function buildDigest(game) {
  const turn = game.watcher?.turn ?? 0;
  const lines = [];
  const pct = (c) => c.hp_max ? Math.round((c.hp / c.hp_max) * 100) : 100;
  const flagBits = (c) => {
    const f = [];
    if (c.hp != null && c.hp_max && pct(c) <= 15) f.push('CRITICAL/near-death');
    else if (c.hp != null && c.hp_max && pct(c) < 40) f.push('badly hurt');
    const st = statusNames(c);
    if (st.length) f.push('status: ' + st.join(', '));
    return f.length ? '  ⚠ ' + f.join('; ') : '';
  };

  const C = game.character;
  if (C?.name) {
    lines.push(`PROTAGONIST — ${C.name}: HP ${C.hp ?? '?'}/${C.hp_max ?? '?'} (${pct(C)}%), MP ${C.mp ?? 0}/${C.mp_max ?? 0}, STA ${C.stamina ?? 0}/${C.stamina_max ?? 0}, Fear ${C.fear_meter ?? 0} (${C.fear_level || 'Calm'}), Rank ${C.rank || 'Unranked'}, ${C.alignment || 'unaligned'}.`);
    lines.push(`  Location: ${locationLabel(game, C.location, C.sublocation)}.`);
    const cf = flagBits(C); if (cf) lines.push(cf);
    if ((C.equipped || []).length) lines.push(`  Equipped: ${C.equipped.map(e => e.name).join(', ')}.`);
    const rels = C.relationships || {};
    const relList = Object.keys(rels).map(n => `${n} ${rels[n].affection >= 0 ? '+' : ''}${rels[n].affection} (${rels[n].status})`);
    if (relList.length) lines.push(`  Feelings toward others: ${relList.join('; ')}.`);
  }

  // Allies (everyone living except the protagonist)
  const allies = allChars(game).filter(x => x.type !== 'player');
  if (allies.length) {
    lines.push('ALLIES (living):');
    allies.forEach(({ ref: a, type }) => {
      const bits = [`HP ${a.hp ?? '?'}/${a.hp_max ?? '?'} (${pct(a)}%)`, locationLabel(game, a.location, a.sublocation)];
      if (a.loyalty != null) bits.push(`loyalty ${a.loyalty}`);
      if (a.alignment) bits.push(a.alignment);
      const towardPlayer = C?.name && a.relationships ? a.relationships[C.name] : null;
      if (towardPlayer) bits.push(`feels ${towardPlayer.status} (${towardPlayer.affection >= 0 ? '+' : ''}${towardPlayer.affection}) toward you`);
      lines.push(`  • ${a.name}${type === 'partner' ? ' [created]' : ''}: ${bits.join(', ')}.${flagBits(a)}`);
    });
  }

  // Active threats
  const enemies = (game.combat?.enemies || []).filter(e => e.alive !== false);
  if (enemies.length) {
    lines.push('ACTIVE THREATS:');
    enemies.forEach(e => lines.push(`  • ${e.name}${e.count > 1 ? ` ×${e.count}` : ''}: HP ${e.hp ?? '?'}/${e.hp_max ?? '?'}, Rank ${(e.rank || 'unranked').toUpperCase()}.`));
  }

  // Running timers / countdowns (turn-based)
  const timers = (game.timers || []).filter(t => t && t.turns_left != null);
  if (timers.length) {
    lines.push('COUNTDOWNS:');
    timers.forEach(t => lines.push(`  • ${t.name}: ${t.turns_left} turn(s) left.${t.turns_left <= 1 ? ' ⚠ ABOUT TO FIRE' : ''}`));
  }

  // Standing reminders the GM most often drops
  const reminders = [];
  allChars(game).forEach(({ ref: c }) => {
    if (hasStatus(c, 'Mortally Wounded')) reminders.push(`${c.name} is Mortally Wounded — this must be addressed, not narrated past.`);
    if (hasStatus(c, 'Encumbered')) reminders.push(`${c.name} is Encumbered — movement/agility is slowed until they drop or store weight.`);
    if (c.loyalty != null && c.loyalty <= 15) reminders.push(`${c.name}'s loyalty is ${c.loyalty} — on the verge of breaking from the team.`);
  });
  if (reminders.length) { lines.push('REMINDERS:'); reminders.forEach(r => lines.push(`  ⚠ ${r}`)); }

  return `[GROUND TRUTH — turn ${turn} — authoritative. This reflects data/game.json RIGHT NOW and overrides anything you think you remember. Narrate consistently with it.]\n${lines.join('\n')}`;
}

// Decrement all turn-based countdowns by one. Returns the timers that expired
// (removed from the list) so the caller can emit "consequence fires now" events.
function tickTimers(g) {
  const expired = [];
  g.timers = (g.timers || []).filter(t => {
    if (t == null || t.turns_left == null) return false;
    t.turns_left -= 1;
    if (t.turns_left <= 0) { expired.push(t); return false; }
    return true;
  });
  return expired;
}

// ── INVARIANT AUDIT ───────────────────────────────────────────
// Runs every tick. Self-heals impossible states and warns ONCE per issue
// (de-duped via game.watcher.audit_seen) so it never spams.
function auditInvariants(game, cron) {
  game.watcher = game.watcher || {};
  const prevSeen = new Set(game.watcher.audit_seen || []);
  const nowSeen = new Set();
  const warnOnce = (key, msg) => { nowSeen.add(key); if (!prevSeen.has(key)) cron.push(msg); };

  const validLocIds = new Set((game.world_map?.locations || []).map(l => l.id));

  allChars(game, true /* include dead */).forEach(({ ref: c }) => {
    const who = c.name || 'unknown';
    // Resource overflow / underflow → clamp (self-healing fires once, then clears)
    for (const [v, mx, lbl] of [['hp','hp_max','HP'], ['mp','mp_max','MP'], ['stamina','stamina_max','stamina']]) {
      if (typeof c[v] === 'number' && typeof c[mx] === 'number') {
        if (c[v] > c[mx]) { cron.push(`WATCHER AUDIT: "${who}" ${lbl} ${c[v]} exceeded max ${c[mx]} — clamped.`); c[v] = c[mx]; }
        if (c[v] < 0)     { cron.push(`WATCHER AUDIT: "${who}" ${lbl} was negative (${c[v]}) — clamped to 0.`); c[v] = 0; }
      }
    }
    // Alive/HP contradiction
    if (c.alive === false && (c.hp ?? 0) > 0) { c.hp = 0; warnOnce(`deadhp:${who}`, `WATCHER AUDIT: "${who}" is marked dead but had HP > 0 — HP set to 0.`); }
    // Ghost equipment — equipped item not in inventory
    (c.equipped || []).forEach(eq => {
      const inInv = (c.items || []).concat(c.weapons || []).some(it =>
        (eq.id != null && it.id === eq.id) || (it.name || '').toLowerCase() === (eq.name || '').toLowerCase());
      if (!inInv) warnOnce(`ghost:${who}:${eq.name}`, `WATCHER AUDIT: "${who}" has "${eq.name}" equipped but it is not in their inventory. Add the item or unequip it.`);
    });
    // Invalid location
    if (c.location && validLocIds.size && !validLocIds.has(c.location))
      warnOnce(`loc:${who}:${c.location}`, `WATCHER AUDIT: "${who}" is at location "${c.location}", which is not on the world map. Move them to a valid location id.`);
    // Affection out of range → clamp
    const rels = c.relationships || {};
    for (const k of Object.keys(rels)) {
      const a = rels[k].affection;
      if (typeof a === 'number' && (a < -100 || a > 100)) {
        rels[k].affection = Math.max(-100, Math.min(100, a));
        rels[k].status = affectionBand(rels[k].affection);
        cron.push(`WATCHER AUDIT: "${who}" affection toward "${k}" was out of range — clamped to ${rels[k].affection}.`);
      }
    }
  });

  game.watcher.audit_seen = [...nowSeen];
}

// ── MAIN TICK ─────────────────────────────────────────────────
let dispatching = false;
let lastDispatchedMsgId = -1;
let gmSessionStarted = false;
let lastGameWrite = 0; // ms timestamp of last successful game.json write

function saveGmState() {
  try {
    fs.writeFileSync(P.gmState, JSON.stringify({ gmSessionStarted, lastDispatchedMsgId }, null, 2));
  } catch (e) {}
}

function loadGmState() {
  const s = readJsonSafe(P.gmState);
  if (!s) return;
  gmSessionStarted = !!s.gmSessionStarted;
  if (typeof s.lastDispatchedMsgId === 'number') lastDispatchedMsgId = s.lastDispatchedMsgId;
  if (gmSessionStarted) log(`AUTO-GM: Restored GM session state (last handled msg #${lastDispatchedMsgId}).`);
}

function tick() {
  const game = readJsonSafe(P.game);
  if (!game) return; // mid-write or missing

  game.watcher = game.watcher || { last_processed_event_id: 0, checkpoint_event_id: 0 };
  game.watcher.running = true;
  game.watcher.last_tick = new Date().toISOString();
  game.watcher.dispatching = dispatching; // kept in sync every tick for the UI

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

  // Invariant audit — self-heal impossible states, warn once per issue
  if (game.character) {
    const auditCron = [];
    try { auditInvariants(game, auditCron); } catch (e) { log('AUDIT ERROR: ' + e.message); }
    if (auditCron.length) { cronBuffer.push(...auditCron); mutated = true; }
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
  // Always write at least every 5s so last_tick stays fresh for the engine status badge
  const needsHeartbeat = (Date.now() - lastGameWrite) > 5000;
  if (mutated || cronBuffer.length || needsHeartbeat) {
    try { writeJson(P.game, game); lastGameWrite = Date.now(); }
    catch (e) { log('WARN: could not write game.json: ' + e.message); }
  }

  // Chat dispatch (auto-GM) — always runs even if game.json write failed
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

function chatBackup() {
  try { if (fs.existsSync(P.chat)) fs.copyFileSync(P.chat, P.chat + '.bak'); } catch(e) {}
}

// Returns true if chat.json is valid; false if it was corrupted (and restored from backup).
function chatValidateAndRestore(msgId) {
  try {
    const raw = fs.readFileSync(P.chat, 'utf8');
    if (!raw || raw.trim() === '') throw new Error('empty file');
    JSON.parse(raw); // throws if malformed
    return true; // all good
  } catch(e) {
    log(`AUTO-GM: chat.json corrupted after msg #${msgId} turn (${e.message}) — restoring backup.`);
    try {
      if (fs.existsSync(P.chat + '.bak')) {
        fs.copyFileSync(P.chat + '.bak', P.chat);
        log('AUTO-GM: chat.json restored from pre-dispatch backup.');
      } else {
        log('AUTO-GM: no backup found — cannot restore.');
      }
    } catch(e2) { log('AUTO-GM: restore failed: ' + e2.message); }
    return false; // was corrupted
  }
}

// ── Immediately stamp dispatching state into game.json ───────
// Called outside the normal tick so the UI sees it within one poll cycle.
function setWatcherPhase(isDispatching) {
  try {
    const g = readJsonSafe(P.game) || {};
    g.watcher = g.watcher || {};
    g.watcher.dispatching = isDispatching;
    writeJson(P.game, g);
    lastGameWrite = Date.now();
  } catch(e) { log('WARN: setWatcherPhase failed: ' + e.message); }
}

function dispatchGM(playerMsg) {
  dispatching = true;
  setWatcherPhase(true);   // immediate — UI sees "GM writing" on next poll
  const useContinue = gmSessionStarted;
  const tool = CFG.settings.ai_tool || 'claude';

  // Snapshot chat.json before the AI touches it — used to restore on corruption
  chatBackup();

  // Advance the turn counter and build the ground-truth digest from the LIVE
  // state. The digest is injected into the prompt so the GM narrates from
  // current facts instead of decayed context (anti-confabulation).
  let digest = '';
  try {
    const g = readJsonSafe(P.game);
    if (g) {
      g.watcher = g.watcher || {};
      g.watcher.turn = (g.watcher.turn || 0) + 1;
      const expired = tickTimers(g);
      writeJson(P.game, g);
      lastGameWrite = Date.now();
      // Emit a directive for each countdown that just hit zero so the GM narrates it.
      if (expired.length) {
        let id = maxEventId(readEventLines()) + 1;
        for (const t of expired) appendCron(`GM DIRECTIVE: Countdown "${t.name}" has reached ZERO — its consequence happens NOW. Narrate it this turn.`, id++);
      }
      digest = buildDigest(g);
    }
  } catch (e) { log('WARN: digest build failed: ' + e.message); }

  log(`AUTO-GM: dispatching player message #${playerMsg.id} to ${tool}${useContinue ? ' (--continue)' : ' (new session)'}`);

  const prompt =
`[WATCHER EVENT] The player sent a new message. Act as the Terror Infinity Game Master.

${digest ? digest + '\n\n' : ''}Steps:
1. Read data/INDEX.md, system/gm-prompt.md, data/game.json, data/chat.json (latest messages), and the tail of data/event-log.txt. The GROUND TRUTH block above is authoritative for current state — trust it over memory.
2. Respond IN CHARACTER. Append your narration as a {"sender":"gm"} message to data/chat.json and set "status":"waiting_for_player".
3. Write EVERY mechanical consequence to data/event-log.txt as "System Message[ID:n]: ..." lines (continue numbering from the highest existing ID). Do NOT compute HP totals, XP, levels, or dice yourself — write the intent events; the watcher computes results.
4. For any uncertain action, write a roll-request event: System Message[ID:n]: Character "NAME" tries to ACTION. Difficulty N. (add [lethal] if failure means death).
5. Read the new Cron Message lines (including any WATCHER WARNING / NOTICE / AUDIT) the watcher left since your last turn, and correct course where they flag a contradiction.

Player message: ${JSON.stringify(playerMsg.content)}`;

  let args;
  let command;
  let extraArgs;
  let useShell = true;

  if (tool === 'opencode') {
    // opencode CLI: `opencode run "message" [--continue] [--model x]`
    command = CFG.settings.opencode_command || 'opencode';
    args = ['run', prompt];
    if (useContinue) args.push('--continue');
    extraArgs = CFG.settings.opencode_extra_args || [];
    if (CFG.settings.ai_model) { args.push('--model'); args.push(CFG.settings.ai_model); }
  } else {
    // claude CLI: pass the prompt via a temp file + stdin redirect.
    // Passing long prompts as -p "arg" through cmd.exe causes truncation/corruption
    // (special chars like quotes, braces, newlines break CMD argument parsing).
    // With shell:true, including '<' in args lets cmd.exe do the redirect natively.
    const tmpFile = path.join(ROOT, 'watcher', '_gm_prompt.tmp');
    fs.writeFileSync(tmpFile, prompt, 'utf8');

    command = CFG.settings.claude_command || 'claude';
    extraArgs = CFG.settings.claude_extra_args || ['--dangerously-skip-permissions'];
    args = ['--print'];
    if (useContinue) args.push('--continue');
    if (CFG.settings.ai_model) { args.push('--model'); args.push(CFG.settings.ai_model); }
    extraArgs.forEach(a => args.push(a));
    extraArgs = []; // already incorporated above
    // Append stdin redirect — cmd.exe (via shell:true) interprets < as a redirect operator
    args.push('<', tmpFile);
    // useShell stays true (cmd.exe processes the < redirect for us)
  }
  extraArgs.forEach(a => args.push(a));

  const child = spawn(command, args, {
    cwd: ROOT, shell: useShell, windowsHide: true,
  });

  let out = '';
  child.stdout.on('data', d => { out += d; });
  child.stderr.on('data', d => { out += d; });

  // ── Hard timeout: kill child if it doesn't exit in time ──
  const GM_TIMEOUT_MS = (CFG.settings.gm_timeout_min || 10) * 60 * 1000;
  let turnDone = false;

  function finishTurn(code, reason) {
    if (turnDone) return;
    turnDone = true;
    clearTimeout(killTimer);
    try { fs.appendFileSync(P.gmLog, `\n===== GM turn (msg #${playerMsg.id}, ${reason}, exit ${code}) ${new Date().toISOString()} =====\n${out}\n`); } catch(e) {}
    if (code === 0 || reason === 'timeout-reply') {
      const chatOk = chatValidateAndRestore(playerMsg.id);
      if (!chatOk) {
        // GM wrote invalid JSON — backup was restored, response is lost.
        // Reset so the watcher re-dispatches as a fresh session.
        log(`AUTO-GM: response for msg #${playerMsg.id} had invalid JSON — resetting for retry.`);
        gmSessionStarted = false;
        lastDispatchedMsgId = playerMsg.id - 1;
        saveGmState();
        dispatching = false;
        setWatcherPhase(false);
        return;
      }
      gmSessionStarted = true;
      log(`AUTO-GM: turn complete (msg #${playerMsg.id})${reason === 'timeout-reply' ? ' [reply detected]' : ''}.`);
      saveGmState();
    } else if (useContinue && !gmSessionStarted) {
      log(`AUTO-GM: --continue failed, retrying as new session.`);
      gmSessionStarted = false; lastDispatchedMsgId = -1; saveGmState();
      dispatching = false;
      setWatcherPhase(false);
      return;
    } else {
      log(`AUTO-GM: ${command} exited ${code} (${reason}). See gm.log.`);
    }
    dispatching = false;
    setWatcherPhase(false); // immediate — UI stops showing "GM writing"
  }

  const killTimer = setTimeout(() => {
    // Before killing, check if the GM actually wrote a reply already
    const chat = readJsonSafe(P.chat);
    const replied = chat && chat.status === 'waiting_for_player';
    if (replied) {
      log(`AUTO-GM: child still running but reply detected — killing child and continuing.`);
      try { child.kill(); } catch(e) {}
      finishTurn(0, 'timeout-reply');
    } else {
      log(`AUTO-GM: timeout after ${GM_TIMEOUT_MS / 60000} min — killing child.`);
      try { child.kill(); } catch(e) {}
      finishTurn(1, 'timeout');
    }
  }, GM_TIMEOUT_MS);

  child.on('close', (code) => finishTurn(code, 'exit'));

  child.on('error', err => {
    log(`AUTO-GM ERROR: ${err.message}. Is '${command}' installed and on PATH?`);
    finishTurn(1, 'error');
  });
}

// ── BOOT ──────────────────────────────────────────────────────
function acquireLock() {
  if (fs.existsSync(P.pidFile)) {
    const oldPid = parseInt(fs.readFileSync(P.pidFile, 'utf8').trim(), 10);
    if (oldPid && oldPid !== process.pid) {
      try {
        process.kill(oldPid, 0); // throws if not running
        console.error(`[TI-Watcher] Another instance is already running (PID ${oldPid}). Exiting.`);
        process.exit(1);
      } catch(e) { /* stale PID — process is gone, safe to take over */ }
    }
  }
  fs.writeFileSync(P.pidFile, String(process.pid));
}

function releaseLock() {
  try { if (fs.existsSync(P.pidFile)) fs.unlinkSync(P.pidFile); } catch(e) {}
}

function boot() {
  acquireLock();
  log('───────────────────────────────────────────────');
  log('Terror Infinity Watcher starting.');
  log(`Project: ${ROOT}`);
  const toolName = CFG.settings.ai_tool || 'claude';
  log(`Auto-GM: ${CFG.settings.auto_gm ? 'ON (' + toolName + ' CLI' + (CFG.settings.ai_model ? ' — ' + CFG.settings.ai_model : '') + ')' : 'OFF (run play terror-infinity manually)'}`);

  loadGmState();

  // Ensure files exist
  if (!fs.existsSync(P.eventLog)) fs.writeFileSync(P.eventLog, '');
  const game = readJsonSafe(P.game);
  if (game) { game.watcher = game.watcher || {}; game.watcher.running = true; writeJson(P.game, game); }

  const interval = CFG.settings.poll_interval_ms || 1500;
  setInterval(() => { try { tick(); } catch (e) { log('TICK ERROR: ' + e.message + '\n' + e.stack); } }, interval);
  log(`Watching every ${interval}ms. Press Ctrl+C to stop.`);
}

process.on('SIGINT',           () => { releaseLock(); const g = readJsonSafe(P.game); if (g?.watcher) { g.watcher.running = false; writeJson(P.game, g); } log('Watcher stopped.'); process.exit(0); });
process.on('exit',             ()  => { releaseLock(); });
process.on('uncaughtException', e  => { log('UNCAUGHT: ' + e.message); releaseLock(); process.exit(1); });

// --once : process a single tick and exit (for testing / harnesses).
if (process.argv.includes('--once')) {
  if (!fs.existsSync(P.eventLog)) fs.writeFileSync(P.eventLog, '');
  try { tick(); } catch (e) { console.error('TICK ERROR:', e.message); }
  process.exit(0);
} else {
  boot();
}
