# DATA INDEX — Where Everything Lives

This is the map of game state. The GM (Claude) and the watcher both read from here.
**Always read this file first if you are unsure where a piece of information lives.**

---

## Authoritative state (read these to know "what is true right now")

| File | Holds | Who writes it |
|------|-------|---------------|
| `data/game.json` | **The single source of truth for current state.** Player character (level, xp, hp, stats, luck, skills, inventory, status effects, fear), guide (Vera), team members, points, phase, movie, watcher cursor. | Watcher (mechanics) + GM (narrative-driven fields) |
| `data/chat.json` | Full message history between player and GM. `status` = `waiting_for_gm` or `waiting_for_player`. | GM (messages) + PHP API (player input) |
| `data/event-log.txt` | **Append-only event journal.** Every mechanical change as a line: `System Message[ID:n]: ...` (GM intent) and `Cron Message[ID:n]: ...` (watcher-computed result). This is the transaction log. | GM writes intents; watcher writes computed results |

## Snapshots (for the death-rewind mechanic)

| File | Holds |
|------|-------|
| `saves/checkpoint.json` | Snapshot of `game.json` taken when the team last entered God's Domain. Restored on player death (first priority). |
| `saves/checkpoint-chat.json` | Snapshot of `chat.json` at the same checkpoint — restored alongside it so the conversation reverts too. |
| `saves/lobby-N.json` | Numbered lobby saves (manual + auto after each movie). |
| `saves/lobby-N.chat.json` | Chat snapshot saved beside each lobby save, so Load restores the conversation as well as the state. |

**Death restore** (`game-api.php?action=player-died`) reverts game + chat + position to the last safe Lobby: auto-checkpoint first, else the newest manual lobby save, else a clean heal-and-reset. The watcher cursor is parked at the end of the event log so old events are not re-applied.

**New game** (`action=new-game`, `mode=keep|new`) wipes progress back to Movie 1: `keep` retains the current character's identity/stats; `new` blanks the character so the GM runs CHARACTER CREATION. The launcher's **CONTINUE** enters the existing game untouched; **START GAME** triggers a new game.

## Static reference (rarely changes)

| File | Holds |
|------|-------|
| `system/movies.json` | All 34 movie scenarios. |
| `system/sounds.json` | Sound-effect tags + Freesound IDs. |
| `system/music.json` | Music library. |
| `system/gm-prompt.md` | The GM's full operating manual. |
| `watcher/config.json` | XP curve, skill→stat map, dice tiers, watcher settings. |
| `world/*.md` | Lore (God's Space, Team Europe). |
| `system/team-gen.json` | Character generation pools: 1689 occupations, 509 hobbies, 17 nationalities with name pools, alignment system, age/gender/build distributions. |
| `system/character-traits.json` | 1000 skills + 200 weaknesses with rarity tiers. 21 physical disabilities flagged `heals_on_movie_end` for the first-movie mercy rule. |
| `system/personality-traits.json` | 100 personality traits (70 positive, 30 negative) for random personality generation. |
| `tools/character_generator.py` | **Character sheet roller.** Reads team-gen + traits + personality to output complete NPC/guide sheets in game.json format. `--guide` for veteran NPCs, `--count N`, `--json`, `--nationality X`, `--gender M/F`. |

---

## How to find a specific fact

- **"What is the player's current HP / stats / level / luck?"** → `data/game.json` → `character`
- **"What's in the player's inventory?"** → `data/game.json` → `character.items` / `character.weapons`
- **"What skills does the player have?"** → `data/game.json` → `character.skills`
- **"Is the guide alive?"** → `data/game.json` → `guide.alive`
- **"Who is on the team and are they alive?"** → `data/game.json` → `team.members[]`
- **"What just happened mechanically?"** → tail of `data/event-log.txt`
- **"What did the player just say?"** → last message in `data/chat.json`
- **"What movie are we in and what are the threats?"** → `game.json.current_movie` → look up in `system/movies.json`
- **"What can God's Space heal?"** → `world/god-space.md` → Death and Restoration section (physical injuries healable for points; first-movie mercy: physical disabilities clear for free)
- **"Does a weakness heal after the movie?"** → `system/character-traits.json` → check `heals_on_movie_end` flag. If true, it's a physical disability that clears on first movie completion (mercy rule) or costs points to heal thereafter.
- **"What level needs how much XP?"** → `watcher/config.json` → `xp_curve_base` (threshold = base × (L−1) × L)

---

## The golden rule for the GM

You do **not** calculate HP totals, XP/level-ups, or dice outcomes. You **write intent events** to `event-log.txt` and the **watcher computes the result** and writes it back. Read the watcher's `Cron Message` lines to learn the outcome, then narrate it. This keeps your attention on story, not math.
