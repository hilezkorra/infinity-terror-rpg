<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { exit; }

$action = $_GET['action'] ?? ($_POST['action'] ?? '');
$base   = __DIR__;

// ── Helper functions ───────────────────────────────────────
function readJson($path) {
    if (!file_exists($path)) return null;
    $raw = file_get_contents($path);
    if ($raw === false || trim($raw) === '') return null;
    return json_decode($raw, true);
}
function writeJson($path, $data) {
    $dir = dirname($path);
    if (!is_dir($dir)) mkdir($dir, 0777, true);
    $json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    if ($json === false) return; // don't wipe file on encode failure
    $tmp = $path . '.phptmp';
    file_put_contents($tmp, $json, LOCK_EX);
    rename($tmp, $path);
}
// Write to chat.json with auto-backup of previous state
function writeChatJson($path, $data) {
    // Keep a rolling backup of the last good chat state before overwriting
    if (file_exists($path)) {
        $bak = $path . '.bak';
        @copy($path, $bak);
    }
    writeJson($path, $data);
}
function nextMsgId($chat) {
    if (empty($chat['messages'])) return 1;
    return max(array_column($chat['messages'], 'id')) + 1;
}

// Highest [ID:n] in the event log — used to park the watcher cursor after a
// restore so it does not re-process (and re-apply) old events.
function maxEventIdFromLog($base) {
    $path = $base . '/data/event-log.txt';
    if (!file_exists($path)) return 0;
    $txt = file_get_contents($path);
    if ($txt === false) return 0;
    if (preg_match_all('/\[ID:(\d+)\]/', $txt, $m)) {
        return max(array_map('intval', $m[1]));
    }
    return 0;
}

// Park the watcher cursor at the current end of the log on a restored game.
function parkWatcherCursor(&$game, $base) {
    $max = maxEventIdFromLog($base);
    $game['watcher'] = $game['watcher'] ?? [];
    $game['watcher']['last_processed_event_id'] = $max;
}

// ── Team / Guide generators ────────────────────────────────
function loadGenData($base) {
    static $cached = null;
    if ($cached === null) $cached = readJson($base . '/system/team-gen.json');
    return $cached;
}
function loadTraits($base) {
    static $cached = null;
    if ($cached === null) $cached = readJson($base . '/system/personality-traits.json');
    return $cached;
}
function pickTraits($base, $count = 5) {
    $data   = loadTraits($base);
    $all    = $data['traits'] ?? [];
    if (empty($all)) return [];
    $pool   = $all;
    $picked = [];
    for ($i = 0; $i < $count && !empty($pool); $i++) {
        $idx      = array_rand($pool);
        $picked[] = ['name' => $pool[$idx]['name'], 'type' => $pool[$idx]['type']];
        array_splice($pool, $idx, 1);
    }
    return $picked;
}
function genRandInt($min, $max) { return random_int((int)$min, (int)$max); }
function weightedPick($items, $weightKey = 'weight') {
    $total = array_sum(array_column($items, $weightKey));
    $r = random_int(1, $total);
    foreach ($items as $item) { $r -= $item[$weightKey]; if ($r <= 0) return $item; }
    return $items[0];
}
function pickWeightedColor($pool, $colorKey, $weightKey) {
    $total = array_sum(array_column($pool, $weightKey));
    $r = random_int(1, $total);
    foreach ($pool as $item) { $r -= $item[$weightKey]; if ($r <= 0) return $item[$colorKey]; }
    return $pool[0][$colorKey];
}
function generatePhysical($nat, $gend, $age, $gen) {
    $male = ($gend === 'Male');
    $hairColor  = pickWeightedColor($nat['hair_colors'], 'c', 'w');
    $eyeColor   = pickWeightedColor($nat['eye_colors'],  'c', 'w');
    $skinTone   = pickWeightedColor($nat['skin_tones'],  't', 'w');
    $hRange     = $male ? $nat['height_male'] : $nat['height_female'];
    $heightCm   = genRandInt($hRange[0], $hRange[1]);
    $build      = weightedPick($gen['builds'])['label'];
    $orientation= weightedPick($gen['sexual_orientations'])['label'];
    return [
        'height_cm'          => $heightCm,
        'hair_color'         => $hairColor,
        'eye_color'          => $eyeColor,
        'skin_tone'          => $skinTone,
        'build'              => $build,
        'sexual_orientation' => $orientation,
    ];
}
function generateMember($base, $forcedNat = null) {
    $gen = loadGenData($base);
    $nat  = $forcedNat ?? weightedPick($gen['nationalities']);
    $gend = weightedPick($gen['genders']);
    $male = ($gend['label'] === 'Male');
    $first = $nat[$male ? 'male' : 'female'][array_rand($nat[$male ? 'male' : 'female'])];
    $last  = $nat['surnames'][array_rand($nat['surnames'])];
    $occ  = $gen['occupations'][array_rand($gen['occupations'])];
    $aln  = weightedPick($gen['alignments']);
    $ageRange = $gen['age_range'];
    $age  = genRandInt($ageRange['min'], $ageRange['max']);
    $attitudes  = $aln['attitudes'];
    $teamStance = $attitudes[array_rand($attitudes)];
    $cities     = $nat['cities'] ?? [];
    $city       = $cities ? $cities[array_rand($cities)] : $nat['country'];
    $str = genRandInt($occ['str'][0], $occ['str'][1]);
    $agi = genRandInt($occ['agi'][0], $occ['agi'][1]);
    $end = genRandInt($occ['end'][0], $occ['end'][1]);
    $int = genRandInt($occ['int'][0], $occ['int'][1]);
    $lck = genRandInt($occ['lck'][0], $occ['lck'][1]);
    $psy = genRandInt($occ['psy'][0], $occ['psy'][1]);
    $hp  = $end * 10;
    $sta = $end * 10;
    $skills = [];
    foreach ($occ['skills'] as $sk) $skills[$sk] = ['level' => 'trained'];
    $physical    = generatePhysical($nat, $gend['label'], $age, $gen);
    $personality = pickTraits($base, 5);
    return [
        'name'                 => $first . ' ' . $last,
        'gender'               => $gend['label'],
        'nationality'          => $nat['country'],
        'city_of_origin'       => $city,
        'age'                  => $age,
        'occupation'           => $occ['label'],
        'physical'             => $physical,
        'personality'          => $personality,
        'alignment'            => $aln['code'],
        'status'               => 'Active',
        'alive'                => true,
        'team_stance'          => $teamStance,
        'location'             => 'hive-train',
        'hp'                   => $hp,
        'hp_max'               => $hp,
        'stamina'              => $sta,
        'stamina_max'          => $sta,
        'level'                => 1,
        'xp'                   => 0,
        'rank'                 => 'Unranked',
        'genetic_locks_opened' => 0,
        'strength'             => $str,
        'agility'              => $agi,
        'endurance'            => $end,
        'intelligence'         => $int,
        'luck'                 => $lck,
        'psyche_force'         => $psy,
        'skills'               => $skills,
        'weapons'              => [],
        'items'                => [],
        'equipped'             => [],
        'status_effects'       => [],
        'relationships'        => (object)[],
    ];
}
function generateRandomTeam($base, $count = 6) {
    $gen   = loadGenData($base);
    $nats  = $gen['nationalities'];
    // Shuffle nationality pool and pick $count distinct ones for variety
    $pool  = $nats;
    $picked = [];
    for ($i = 0; $i < min($count, count($pool)); $i++) {
        $idx = array_rand($pool);
        $picked[] = $pool[$idx];
        array_splice($pool, $idx, 1);
    }
    $members = [];
    for ($i = 0; $i < $count; $i++) {
        $nat = isset($picked[$i]) ? $picked[$i] : null;
        $members[] = generateMember($base, $nat);
    }
    return $members;
}
function generateGuideProfile($base) {
    $gen  = loadGenData($base);
    $nat  = weightedPick($gen['nationalities']);
    $gend = weightedPick($gen['genders']);
    $male = ($gend['label'] === 'Male');
    $first = $nat[$male ? 'male' : 'female'][array_rand($nat[$male ? 'male' : 'female'])];
    $last  = $nat['surnames'][array_rand($nat['surnames'])];
    $occ  = $gen['guide_occupations'][array_rand($gen['guide_occupations'])];
    $ageR = $gen['guide_ages'];
    $age  = genRandInt($ageR['min'], $ageR['max']);
    $str = genRandInt($occ['str'][0], $occ['str'][1]);
    $agi = genRandInt($occ['agi'][0], $occ['agi'][1]);
    $end = genRandInt($occ['end'][0], $occ['end'][1]);
    $int = genRandInt($occ['int'][0], $occ['int'][1]);
    $lck = genRandInt($occ['lck'][0], $occ['lck'][1]);
    $psy = genRandInt($occ['psy'][0], $occ['psy'][1]);
    $hp  = $end * 10;
    $sta = $end * 10;
    $survived = genRandInt($gen['guide_survived_movies']['min'], $gen['guide_survived_movies']['max']);
    $skills = [];
    foreach ($occ['skills'] as $sk) $skills[$sk] = ['level' => 'expert'];
    return [
        'name'                 => $first . ' ' . $last,
        'gender'               => $gend['label'],
        'nationality'          => $nat['country'],
        'age'                  => $age,
        'occupation'           => $occ['label'],
        'alive'                => true,
        'movies_survived'      => $survived,
        'death_movie'          => null,
        'death_description'    => null,
        'introduced'           => false,
        'knowledge'            => ['exchange terminal basics', 'God\'s Space rules', 'survival fundamentals'],
        'personality'          => ['humor' => 'Dry', 'composure' => 'Steady', 'disposition' => 'Direct'],
        'quirk'                => '',
        'backstory'            => '',
        'strength'             => $str,
        'agility'              => $agi,
        'endurance'            => $end,
        'intelligence'         => $int,
        'luck'                 => $lck,
        'psyche_force'         => $psy,
        'level'                => $survived + 1,
        'xp'                   => $survived * 500,
        'hp'                   => $hp,
        'hp_max'               => $hp,
        'mp'                   => 0,
        'mp_max'               => 0,
        'stamina'              => $sta,
        'stamina_max'          => $sta,
        'rank'                 => 'F',
        'genetic_locks_opened' => min($survived, 3),
        'skills'               => $skills,
        'enhancements'         => [],
    ];
}

// Reset a game state to a fresh Movie-1 start. Progress is wiped; identity is
// kept unless $newCharacter is true (then it's blanked for GM-driven creation).
function freshGameState($game, $newCharacter) {
    // ── World / run ──
    $game['phase']                    = 'movie';
    $game['setup_step']               = null;
    $game['current_movie']            = 'resident-evil';
    $game['movie_number']             = 1;
    $game['movie_start_message_id']   = 1;
    $game['points']                   = 100;
    $game['deaths']                   = 0;
    $game['total_survived']           = 0;
    $game['world_day']                = 1;
    $game['lobby_save_index']         = 0;
    $game['last_lobby_save']          = null;
    $game['system_attention']         = 0;
    $game['movie_difficulty_modifier']= 0;
    $game['creation_used']            = false;
    $game['enemy_team']               = null;
    $game['partners']                 = [];
    $game['combat']                   = ['active' => false, 'enemies' => []];
    $game['movie_performance']        = ['deaths' => 0, 'objectives_completed' => 0, 'meta_exploits_detected' => 0, 'time_used_pct' => 0];
    unset($game['timers']);
    $game['watcher'] = ['last_processed_event_id' => 0, 'checkpoint_event_id' => 0, 'turn' => 0, 'running' => false];

    // ── Character: keep identity + base, wipe progress ──
    $c = $game['character'] ?? [];
    $c['level']                 = 1;
    $c['xp']                    = 0;
    $c['genetic_locks_opened']  = 0;
    $c['rank']                  = 'Unranked';
    $c['kills']                 = 0;
    $c['movies_survived']       = 0;
    if (isset($c['hp_max']))      $c['hp'] = $c['hp_max'];
    if (isset($c['mp_max']))      $c['mp'] = $c['mp_max'];
    if (isset($c['stamina_max'])) $c['stamina'] = $c['stamina_max'];
    $c['fear_meter']            = 0;
    $c['fear_level']            = 'Calm';
    $c['status_effects']        = [];
    $c['relationships']         = (object)[];
    $c['equipped']              = [];
    $c['location']              = 'hive-train';
    unset($c['sublocation']);
    unset($c['storage']);

    if ($newCharacter) {
        // Blank the identity so the UI shows "creation pending" and the GM
        // runs a character-creation conversation before the movie opens.
        $c['name']        = '';
        $c['age']         = null;
        $c['nationality'] = '';
        $c['background']  = '';
        $c['occupation']  = '';
        $c['backstory']   = '';
    }
    $game['character'] = $c;

    // Reset team member locations to movie starting point
    if (isset($game['team']['members'])) {
        foreach ($game['team']['members'] as &$member) {
            $member['location'] = 'hive-train';
            unset($member['sublocation']);
        }
        unset($member);
    }

    return $game;
}

// A fresh intro chat for a new game.
function canonicalIntroChat($newCharacter) {
    $content = $newCharacter
        ? "GOD'S SPACE — NEW ARRIVAL DETECTED. Before the door opens, tell me who you were in the world you left: your name, where you're from, and what you did. (Describe your character to begin.)"
        : "GOD'S SPACE — MOVIE ENTRY LOGGED";
    return [
        'status'   => 'waiting_for_player',
        'messages' => [[
            'id'        => 1,
            'sender'    => 'system',
            'content'   => $content,
            'timestamp' => date('c'),
        ]],
    ];
}

// ── Get game state ─────────────────────────────────────────
if ($action === 'get-state') {
    $game = readJson($base . '/data/game.json');
    echo json_encode($game ?: ['error' => 'No game state found']);
    exit;
}

// ── Get chat ──────────────────────────────────────────────
if ($action === 'get-chat') {
    $chat = readJson($base . '/data/chat.json');
    echo json_encode($chat ?: ['messages' => [], 'status' => 'error']);
    exit;
}

// ── Get movies list ───────────────────────────────────────
if ($action === 'get-movies') {
    $movies = readJson($base . '/system/movies.json');
    echo json_encode($movies ?: ['error' => 'No movies found']);
    exit;
}

// ── Get sounds ────────────────────────────────────────────
if ($action === 'get-sounds') {
    $sounds = readJson($base . '/system/sounds.json');
    echo json_encode($sounds ?: ['error' => 'No sounds found']);
    exit;
}

// ── Get music ─────────────────────────────────────────────
if ($action === 'get-music') {
    $music = readJson($base . '/system/music.json');
    echo json_encode($music ?: ['error' => 'No music found']);
    exit;
}

// ── Send player command ────────────────────────────────────
if ($action === 'send-command' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $chatFile = $base . '/data/chat.json';
    $input    = json_decode(file_get_contents('php://input'), true);
    $command  = trim($input['command'] ?? '');
    if (!$command) { http_response_code(400); echo json_encode(['error' => 'No command']); exit; }
    if (!file_exists($chatFile)) { http_response_code(500); echo json_encode(['error' => 'Chat missing']); exit; }

    $chat = readJson($chatFile);
    $msg  = [
        'id'        => nextMsgId($chat),
        'sender'    => 'player',
        'content'   => $command,
        'timestamp' => date('c'),
    ];
    $chat['messages'][] = $msg;
    $chat['status']     = 'waiting_for_gm';
    writeChatJson($chatFile, $chat);
    echo json_encode(['ok' => true, 'message' => $msg]);
    exit;
}

// ── Mark a room as explored (fog-of-war) ─────────────────
if ($action === 'explore-room' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $input    = json_decode(file_get_contents('php://input'), true);
    $floorId  = $input['floorId'] ?? '';
    $roomId   = $input['roomId']  ?? '';
    if (!$floorId || !$roomId) { http_response_code(400); echo json_encode(['error'=>'Missing params']); exit; }

    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error'=>'No game state']); exit; }

    if (!isset($game['world_map']['canvas_map']['floors'][$floorId])) {
        echo json_encode(['ok'=>false,'error'=>'Floor not found']); exit;
    }
    $floor = &$game['world_map']['canvas_map']['floors'][$floorId];

    if (!isset($floor['explored'])) $floor['explored'] = [];
    if (!in_array($roomId, $floor['explored'])) {
        $floor['explored'][] = $roomId;
        writeJson($gameFile, $game);
    }
    echo json_encode(['ok' => true]);
    exit;
}

// ── Interact with a map object ────────────────────────────
if ($action === 'interact-object' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $chatFile = $base . '/data/chat.json';
    $input    = json_decode(file_get_contents('php://input'), true);
    $floorId  = $input['floorId']   ?? '';
    $roomId   = $input['roomId']    ?? '';
    $objId    = $input['objId']     ?? '';
    $verb     = strtolower(trim($input['verb'] ?? 'examine'));
    $label    = $input['label']     ?? $objId;
    $roomLabel= $input['roomLabel'] ?? $roomId;

    if (!$roomId || !$objId) {
        http_response_code(400); echo json_encode(['error' => 'Missing roomId or objId']); exit;
    }

    // Map verb → new state (null = examine, no state change)
    $stateMap = [
        'search'            => 'searched',
        'search body'       => 'searched',
        'loot'              => 'searched',
        'take'              => 'searched',
        'take weapon'       => 'partial',
        'read'              => 'searched',
        'use terminal'      => null,
        'use'               => null,
        'hack'              => null,
        'bypass'            => null,
        'activate'          => 'active',
        'open'              => 'open',
        'force open'        => 'open',
        'break open'        => 'broken',
        'pick lock'         => 'unlocked',
        'unlock'            => 'unlocked',
        'listen'            => null,
        'speak'             => null,
        'check vitals'      => null,
        'initiate revival'  => null,
        'interact'          => null,
        'cut power'         => 'inactive',
        'examine'           => null,
    ];
    $newState = array_key_exists($verb, $stateMap) ? $stateMap[$verb] : null;

    // Update object state in game.json
    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error' => 'No game state']); exit; }

    $found = false;
    $floors = &$game['world_map']['canvas_map']['floors'];
    foreach ($floors as $fid => &$floor) {
        foreach ($floor['rooms'] as &$room) {
            if ($room['id'] !== $roomId) continue;
            foreach (($room['objects'] ?? []) as &$obj) {
                if ($obj['id'] !== $objId) continue;
                $found = true;
                // Don't overwrite terminal states with null, don't "un-search" already searched
                if ($newState !== null) {
                    $locked   = in_array($obj['state'], ['searched','used','broken','breached']);
                    if (!$locked) $obj['state'] = $newState;
                }
                break 3;
            }
            break 2;
        }
    }
    if (!$found) { echo json_encode(['ok'=>false,'error'=>'Object not found']); exit; }
    writeJson($gameFile, $game);

    // Build natural-language command for the GM
    $verbPhrases = [
        'examine'          => 'examine',          'search'      => 'search through',
        'search body'      => 'search the body of','loot'        => 'loot',
        'take'             => 'take',              'take weapon' => 'take a weapon from',
        'read'             => 'read',              'use terminal'=> 'use',
        'use'              => 'use',               'hack'        => 'attempt to hack',
        'bypass'           => 'attempt to bypass', 'activate'    => 'try to activate',
        'open'             => 'open',              'force open'  => 'force open',
        'break open'       => 'break open',        'pick lock'   => 'pick the lock on',
        'unlock'           => 'unlock',            'listen'      => 'listen to',
        'speak'            => 'speak into',        'check vitals'=> 'check the vitals on',
        'initiate revival' => 'initiate the revival sequence on','interact'=>'interact with',
        'cut power'        => 'cut power at',
    ];
    $phrase  = $verbPhrases[$verb] ?? $verb;
    $command = "I {$phrase} the {$label} in the {$roomLabel}.";

    // Append to chat so the GM watcher picks it up
    if (!file_exists($chatFile)) { echo json_encode(['ok'=>false,'error'=>'No chat file']); exit; }
    $chat = readJson($chatFile);
    $msg  = [
        'id'        => nextMsgId($chat),
        'sender'    => 'player',
        'content'   => $command,
        'timestamp' => date('c'),
    ];
    $chat['messages'][] = $msg;
    $chat['status']     = 'waiting_for_gm';
    writeChatJson($chatFile, $chat);

    echo json_encode(['ok' => true, 'command' => $command, 'newState' => $newState]);
    exit;
}

// ── Next turn ─────────────────────────────────────────────
if ($action === 'next-turn' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error'=>'No game state']); exit; }

    $combat = &$game['combat'];
    $n = count($combat['combatants'] ?? []);
    if ($n > 0) {
        $next = (($combat['turn_index'] ?? 0) + 1) % $n;
        if ($next === 0) $combat['round'] = ($combat['round'] ?? 1) + 1;
        $combat['turn_index'] = $next;
    }
    writeJson($gameFile, $game);
    echo json_encode(['ok'=>true, 'turn_index'=>$combat['turn_index'], 'round'=>$combat['round']]);
    exit;
}

// ── Prev turn ─────────────────────────────────────────────
if ($action === 'prev-turn' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error'=>'No game state']); exit; }

    $combat = &$game['combat'];
    $n = count($combat['combatants'] ?? []);
    if ($n > 0) {
        $prev = (($combat['turn_index'] ?? 0) - 1 + $n) % $n;
        if ($prev === $n - 1 && ($combat['round'] ?? 1) > 1) $combat['round']--;
        $combat['turn_index'] = $prev;
    }
    writeJson($gameFile, $game);
    echo json_encode(['ok'=>true, 'turn_index'=>$combat['turn_index'], 'round'=>$combat['round']]);
    exit;
}

// ── Set combat state (GM) ─────────────────────────────────
if ($action === 'set-combat' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $game  = readJson($gameFile);
    $input = json_decode(file_get_contents('php://input'), true) ?? [];
    if (!$game) { http_response_code(500); echo json_encode(['error'=>'No game state']); exit; }

    $combat = &$game['combat'];
    if (isset($input['active']))      $combat['active']      = (bool)$input['active'];
    if (isset($input['round']))       $combat['round']       = (int)$input['round'];
    if (isset($input['turn_index']))  $combat['turn_index']  = (int)$input['turn_index'];
    if (isset($input['location']))    $combat['location']    = $input['location'];
    if (isset($input['combatants']))  $combat['combatants']  = $input['combatants'];
    if (isset($input['combat_log']))  $combat['combat_log']  = $input['combat_log'];

    writeJson($gameFile, $game);
    echo json_encode(['ok'=>true, 'combat'=>$combat]);
    exit;
}

// ── GM narrate — appends a line to combat.combat_log ─────
if ($action === 'gm-narrate' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $game  = readJson($gameFile);
    $input = json_decode(file_get_contents('php://input'), true) ?? [];
    if (!$game) { http_response_code(500); echo json_encode(['error'=>'No game state']); exit; }
    $text = trim($input['text'] ?? '');
    if ($text === '') { echo json_encode(['ok'=>true]); exit; }
    if (!isset($game['combat']['combat_log']) || !is_array($game['combat']['combat_log']))
        $game['combat']['combat_log'] = [];
    $game['combat']['combat_log'][] = '[GM] ' . $text;
    writeJson($gameFile, $game);
    echo json_encode(['ok'=>true]);
    exit;
}

// ── Save lobby state ──────────────────────────────────────
if ($action === 'save-lobby' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error' => 'No game state']); exit; }

    $idx = ($game['lobby_save_index'] ?? 0) + 1;
    $savePath = $base . '/saves/lobby-' . $idx . '.json';

    // Save current game state + a chat snapshot sidecar so the conversation
    // can be restored on load.
    writeJson($savePath, $game);
    $chat = readJson($base . '/data/chat.json');
    if ($chat) writeJson($base . '/saves/lobby-' . $idx . '.chat.json', $chat);

    // Update game with new save index
    $game['lobby_save_index']  = $idx;
    $game['last_lobby_save']   = 'saves/lobby-' . $idx . '.json';
    writeJson($gameFile, $game);

    echo json_encode(['ok' => true, 'save_path' => $game['last_lobby_save'], 'index' => $idx]);
    exit;
}

// ── Start a NEW game (reset progress) ─────────────────────
// mode=keep  → replay with the existing character (identity kept, progress wiped)
// mode=new   → blank the character for GM-driven creation
if ($action === 'new-game' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $chatFile = $base . '/data/chat.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $mode       = $input['mode']       ?? ($_GET['mode']       ?? 'keep');   // keep | new
    $teamMode   = $input['team_mode']  ?? ($_GET['team_mode']  ?? 'keep');   // keep | generate
    $guideMode  = $input['guide_mode'] ?? ($_GET['guide_mode'] ?? 'keep');   // keep | generate | blank
    $newCharacter = ($mode === 'new');

    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error' => 'No game state to reset']); exit; }

    $game = freshGameState($game, $newCharacter);

    // Team regeneration
    if ($teamMode === 'generate') {
        $game['team']['members'] = generateRandomTeam($base);
    } elseif (empty($game['team']['members'])) {
        // Auto-generate if team is empty (e.g. very first run)
        $game['team']['members'] = generateRandomTeam($base);
    }

    // Guide regeneration / blank
    if ($guideMode === 'generate') {
        $game['guide'] = generateGuideProfile($base);
    } elseif ($guideMode === 'blank') {
        $game['guide']['name']        = '';
        $game['guide']['nationality'] = '';
        $game['guide']['occupation']  = '';
        $game['guide']['backstory']   = '';
        $game['guide']['introduced']  = false;
        $game['guide']['knowledge']   = [];
        $game['guide']['personality'] = (object)[];
    }

    writeJson($gameFile, $game);

    // Fresh chat + empty event log so the watcher starts clean.
    writeChatJson($chatFile, canonicalIntroChat($newCharacter));
    file_put_contents($base . '/data/event-log.txt', '');

    // Drop any old auto-checkpoint so a death right after a new game can't
    // restore the previous run. (Manual lobby-N saves are kept on purpose.)
    @unlink($base . '/saves/checkpoint.json');
    @unlink($base . '/saves/checkpoint-chat.json');

    echo json_encode(['ok' => true, 'mode' => $mode, 'team_mode' => $teamMode, 'guide_mode' => $guideMode]);
    exit;
}

// ── Restore on player death ───────────────────────────────
// Full restore to the last safe Lobby state: game + chat + position all revert.
// Priority: watcher auto-checkpoint → newest manual lobby save → clean reset.
if ($action === 'player-died' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile  = $base . '/data/game.json';
    $chatFile  = $base . '/data/chat.json';
    $game = readJson($gameFile);
    if (!$game) { http_response_code(500); echo json_encode(['error' => 'No game state']); exit; }
    $deaths = ($game['deaths'] ?? 0) + 1;

    // Resolve a snapshot pair {game, chat} to restore from.
    $snapGame = null; $snapChat = null; $restoredFrom = null;

    $chkGame = $base . '/saves/checkpoint.json';
    $chkChat = $base . '/saves/checkpoint-chat.json';
    if (file_exists($chkGame)) {
        $snapGame = readJson($chkGame);
        $snapChat = file_exists($chkChat) ? readJson($chkChat) : null;
        $restoredFrom = 'checkpoint';
    } else {
        // The current run's manual lobby save, if one exists. (We deliberately
        // do NOT scan the saves folder — that could restore a previous run's
        // save after a New Game. New Game nulls last_lobby_save.)
        $lp = $game['last_lobby_save'] ?? null;
        if ($lp && file_exists($base . '/' . $lp)) {
            $lobbyPath = $base . '/' . $lp;
            $snapGame = readJson($lobbyPath);
            $chatSidecar = preg_replace('/\.json$/', '.chat.json', $lobbyPath);
            $snapChat = file_exists($chatSidecar) ? readJson($chatSidecar) : null;
            $restoredFrom = basename($lobbyPath);
        }
    }

    if ($snapGame) {
        // Full state revert
        $snapGame['deaths']                 = $deaths;
        $snapGame['phase']                  = 'lobby';
        $snapGame['current_movie']          = null;
        $snapGame['movie_start_message_id'] = null;
        $snapGame['combat']                 = ['enemies' => [], 'active' => false];
        unset($snapGame['timers']);
        parkWatcherCursor($snapGame, $base); // don't re-apply post-checkpoint events
        writeJson($gameFile, $snapGame);

        // Chat reverts to the snapshot (this is what "removes the chat")
        $chat = $snapChat ?: readJson($chatFile) ?: ['messages' => []];
        $chat['messages'][] = [
            'id'        => nextMsgId($chat),
            'sender'    => 'system',
            'content'   => 'CONSCIOUSNESS RESTORED — Death registered. Body reconstituted from the last Lobby checkpoint; everything after it is undone. Deaths total: ' . $deaths,
            'timestamp' => date('c'),
        ];
        $chat['status'] = 'waiting_for_gm';
        writeChatJson($chatFile, $chat);

        echo json_encode(['ok' => true, 'restored_from' => $restoredFrom, 'deaths' => $deaths]);
        exit;
    }

    // No snapshot at all → clean reset (heal, clear, drop position/threats) + fresh chat
    $c = $game['character'] ?? [];
    if (isset($c['hp_max']))      $c['hp'] = $c['hp_max'];
    if (isset($c['mp_max']))      $c['mp'] = $c['mp_max'];
    if (isset($c['stamina_max'])) $c['stamina'] = $c['stamina_max'];
    $c['fear_meter'] = 0; $c['fear_level'] = 'Calm';
    $c['status_effects'] = [];
    $c['location'] = 'entrance-hall';
    unset($c['sublocation']);
    $game['character'] = $c;
    $game['deaths'] = $deaths;
    $game['phase'] = 'lobby';
    $game['current_movie'] = null;
    $game['movie_start_message_id'] = null;
    $game['combat'] = ['enemies' => [], 'active' => false];
    unset($game['timers']);
    parkWatcherCursor($game, $base);
    writeJson($gameFile, $game);

    $chat = ['status' => 'waiting_for_gm', 'messages' => [[
        'id' => 1, 'sender' => 'system',
        'content' => 'CONSCIOUSNESS RESTORED — Death registered, but no Lobby checkpoint existed. You wake disoriented at the threshold, your wounds gone. Deaths total: ' . $deaths,
        'timestamp' => date('c'),
    ]]];
    writeChatJson($chatFile, $chat);

    echo json_encode(['ok' => true, 'restored_from' => 'clean-reset', 'deaths' => $deaths]);
    exit;
}

// ── Load a specific save file ─────────────────────────────
if ($action === 'load-save' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $gameFile = $base . '/data/game.json';
    $chatFile = $base . '/data/chat.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $file = basename(trim($input['file'] ?? ''));
    if (!$file || !str_starts_with($file, 'lobby-') || !str_ends_with($file, '.json')) {
        http_response_code(400); echo json_encode(['error' => 'Invalid save file']); exit;
    }
    $savePath = $base . '/saves/' . $file;
    if (!file_exists($savePath)) {
        http_response_code(404); echo json_encode(['error' => 'Save file not found']); exit;
    }
    $savedGame = readJson($savePath);
    if (!$savedGame) {
        http_response_code(500); echo json_encode(['error' => 'Cannot read save file']); exit;
    }
    // Restore game state from the chosen save.
    $game = readJson($gameFile);
    $deaths = ($game['deaths'] ?? 0);
    $savedGame['deaths'] = $deaths;
    $savedGame['phase']  = 'lobby';
    $savedGame['current_movie'] = null;
    $savedGame['movie_start_message_id'] = null;
    $savedGame['combat'] = ['enemies' => [], 'active' => false];
    unset($savedGame['timers']);
    parkWatcherCursor($savedGame, $base);
    writeJson($gameFile, $savedGame);

    // Restore the chat snapshot saved alongside this slot (if present);
    // otherwise keep the current chat.
    $sidecar = preg_replace('/\.json$/', '.chat.json', $savePath);
    $chat = file_exists($sidecar) ? readJson($sidecar) : readJson($chatFile);
    if (!$chat) $chat = ['messages' => []];
    $chat['messages'][] = [
        'id'        => nextMsgId($chat),
        'sender'    => 'system',
        'content'   => 'Save restored from ' . $file . '. Welcome back to God\'s Space.',
        'timestamp' => date('c'),
    ];
    $chat['status'] = 'waiting_for_player';
    writeChatJson($chatFile, $chat);

    echo json_encode(['ok' => true, 'restored_from' => $file]);
    exit;
}

// ── List lobby saves ──────────────────────────────────────
if ($action === 'list-saves') {
    $saves = [];
    $savesDir = $base . '/saves/';
    if (is_dir($savesDir)) {
        foreach (glob($savesDir . 'lobby-*.json') as $f) {
            if (str_ends_with($f, '.chat.json')) continue; // skip chat sidecars
            $data = readJson($f);
            $saves[] = [
                'file'        => basename($f),
                'movie_num'   => $data['movie_number'] ?? 0,
                'points'      => $data['points'] ?? 0,
                'char_name'   => $data['character']['name'] ?? 'Unknown',
                'phase'       => $data['phase'] ?? 'unknown',
                'mtime'       => filemtime($f),
            ];
        }
        usort($saves, fn($a,$b) => $b['mtime'] - $a['mtime']);
    }
    echo json_encode(['saves' => $saves]);
    exit;
}

// ── Update game state field (for UI direct updates) ────────
// ── Save a Freesound ID for a sound key ──────────────────
if ($action === 'save-sound-id' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $soundsFile = $base . '/system/sounds.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $key  = trim($input['key']  ?? '');
    $fsId = $input['id']; // may be null to clear

    if (!$key) { http_response_code(400); echo json_encode(['error' => 'No key']); exit; }

    $sounds = readJson($soundsFile);
    if (!$sounds) {
        http_response_code(500); echo json_encode(['error' => 'Cannot read sounds file']); exit;
    }
    // Auto-create entry if key doesn't exist
    if (!isset($sounds['sounds'][$key])) {
        $sounds['sounds'][$key] = [
            'label' => $key,
            'description' => '',
            'freesound_id' => null,
            'audio_url' => null,
        ];
    }
    // Ensure loop defaults to true
    if (!isset($sounds['sounds'][$key]['loop'])) {
        $sounds['sounds'][$key]['loop'] = true;
    }

    $sounds['sounds'][$key]['freesound_id'] = $fsId ? (int)$fsId : null;
    // Save loop toggle if provided
    if (isset($input['loop'])) {
        $sounds['sounds'][$key]['loop'] = (bool)$input['loop'];
    }
    // Also save direct audio URL if provided
    $audioUrl = trim($input['audio_url'] ?? '');
    $sounds['sounds'][$key]['audio_url'] = $audioUrl ?: null;
    writeJson($soundsFile, $sounds);
    echo json_encode(['ok' => true, 'key' => $key, 'id' => $fsId ? (int)$fsId : null, 'audio_url' => $audioUrl ?: null]);
    exit;
}

// ── Save YouTube ID for a music track ────────────────────
if ($action === 'save-music-id' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $musicFile = $base . '/system/music.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $index = (int)($input['index'] ?? -1);
    $ytId  = trim($input['youtube_id'] ?? '');

    $music = readJson($musicFile);
    if (!$music || !isset($music['tracks'][$index])) {
        http_response_code(404); echo json_encode(['error' => 'Track not found']); exit;
    }

    $music['tracks'][$index]['youtube_id'] = $ytId ?: null;
    writeJson($musicFile, $music);
    echo json_encode(['ok' => true, 'index' => $index, 'youtube_id' => $ytId ?: null]);
    exit;
}

// ── Fetch YouTube video info (server-side, avoids CORS) ───
if ($action === 'fetch-yt-info') {
    $url = urldecode($_GET['url'] ?? '');
    if (!$url || !preg_match('/youtube\.com|youtu\.be/', $url)) {
        http_response_code(400); echo json_encode(['error' => 'Invalid YouTube URL']); exit;
    }
    $oembedUrl = 'https://www.youtube.com/oembed?url=' . urlencode($url) . '&format=json';
    $ctx = stream_context_create(['http' => ['timeout' => 8, 'user_agent' => 'Mozilla/5.0 (compatible)']]);
    $res = @file_get_contents($oembedUrl, false, $ctx);
    if (!$res) { http_response_code(502); echo json_encode(['error' => 'Could not reach YouTube. Check the URL is public.']); exit; }
    $data = json_decode($res, true);
    preg_match('/(?:v=|youtu\.be\/|embed\/)([A-Za-z0-9_\-]{11})/', $url, $m);
    echo json_encode([
        'title'    => $data['title'] ?? '',
        'author'   => $data['author_name'] ?? '',
        'video_id' => $m[1] ?? null,
    ]);
    exit;
}

// ── Replace MUSIC-SEARCH tag with MUSIC tag in chat ──────
if ($action === 'replace-music-search' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $chatFile = $base . '/data/chat.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $searchQuery = trim($input['search_query'] ?? '');
    $trackId = trim($input['track_id'] ?? '');
    if (!$searchQuery || !$trackId) {
        http_response_code(400); echo json_encode(['error' => 'Missing search_query or track_id']); exit;
    }
    $chat = readJson($chatFile);
    if (!$chat) { http_response_code(500); echo json_encode(['error' => 'Cannot read chat.json']); exit; }
    $changed = false;
    foreach ($chat['messages'] as &$msg) {
        if ($msg['sender'] === 'gm' && strpos($msg['content'], '[MUSIC-SEARCH:' . $searchQuery . ']') !== false) {
            $msg['content'] = str_replace('[MUSIC-SEARCH:' . $searchQuery . ']', '[MUSIC:' . $trackId . ']', $msg['content']);
            $changed = true;
        }
    }
    if ($changed) writeChatJson($chatFile, $chat);
    echo json_encode(['ok' => true, 'changed' => $changed]);
    exit;
}

// ── Add a single music track ──────────────────────────────
if ($action === 'add-music' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $musicFile = $base . '/system/music.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $music = readJson($musicFile);
    if (!$music) { http_response_code(500); echo json_encode(['error' => 'Cannot read music.json']); exit; }

    $ytId = trim($input['youtube_id'] ?? '');
    $title = trim($input['title'] ?? 'Unknown');
    $artist = trim($input['artist'] ?? 'Unknown');

    // Prevent duplicates by youtube_id
    if ($ytId) {
        foreach ($music['tracks'] as $t) {
            if (($t['youtube_id'] ?? '') === $ytId) {
                echo json_encode(['ok' => false, 'error' => 'Track already in library', 'track' => $t]);
                exit;
            }
        }
    }

    $track = [
        'id'           => 'custom-' . ($ytId ?: uniqid()),
        'title'        => $title,
        'artist'       => $artist,
        'category'     => $input['category'] ?? 'Custom',
        'youtube_id'   => $ytId ?: null,
        'search_query' => $title . ' ' . $artist,
        'mood'         => $input['mood'] ?? '',
        'bpm'          => '',
        'custom'       => true,
    ];
    $music['tracks'][] = $track;
    // Ensure 'Custom' is in categories
    if (!in_array('Custom', $music['categories'] ?? [])) {
        $music['categories'][] = 'Custom';
    }
    writeJson($musicFile, $music);
    echo json_encode(['ok' => true, 'track' => $track]);
    exit;
}

// ── Remove a music track ──────────────────────────────────
if ($action === 'remove-music' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $musicFile = $base . '/system/music.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $trackId = $input['id'] ?? '';
    if (!$trackId) { http_response_code(400); echo json_encode(['error' => 'No id']); exit; }
    $music = readJson($musicFile);
    if (!$music) { http_response_code(500); echo json_encode(['error' => 'Cannot read music.json']); exit; }
    $before = count($music['tracks'] ?? []);
    $music['tracks'] = array_values(array_filter($music['tracks'] ?? [], fn($t) => ($t['id'] ?? '') !== $trackId));
    writeJson($musicFile, $music);
    echo json_encode(['ok' => true, 'removed' => $before - count($music['tracks'])]);
    exit;
}

// ── Add all videos from a YouTube playlist ────────────────
if ($action === 'add-playlist' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $musicFile = $base . '/system/music.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $rawUrl = trim($input['url'] ?? '');
    $category = $input['category'] ?? 'Custom';

    preg_match('/[?&]list=([A-Za-z0-9_\-]+)/', $rawUrl, $pm);
    $playlistId = $pm[1] ?? null;
    if (!$playlistId) { http_response_code(400); echo json_encode(['error' => 'Could not find playlist ID in URL. Make sure the URL contains ?list=...']); exit; }

    $rssUrl = 'https://www.youtube.com/feeds/videos.xml?playlist_id=' . urlencode($playlistId);
    $ctx = stream_context_create(['http' => ['timeout' => 12, 'user_agent' => 'Mozilla/5.0 (compatible)']]);
    $rss = @file_get_contents($rssUrl, false, $ctx);
    if (!$rss) { http_response_code(502); echo json_encode(['error' => 'Could not fetch playlist. Make sure it is public and the URL is correct.']); exit; }

    libxml_use_internal_errors(true);
    $xml = simplexml_load_string($rss);
    if (!$xml) { http_response_code(502); echo json_encode(['error' => 'Could not parse playlist XML']); exit; }

    $music = readJson($musicFile);
    if (!$music) { http_response_code(500); echo json_encode(['error' => 'Cannot read music.json']); exit; }

    // Build existing ID set to avoid duplicates
    $existingIds = array_column($music['tracks'] ?? [], 'youtube_id');

    $added = []; $skipped = 0;
    foreach ($xml->entry as $entry) {
        $ns = $entry->getNamespaces(true);
        $ytNs = array_filter(array_keys($ns), fn($k) => $k === 'yt');
        $ytKey = reset($ytNs) ?: 'yt';
        $ytEl = $entry->children($ns[$ytKey] ?? 'http://www.youtube.com/xml/schemas/2015');
        $videoId = (string)($ytEl->videoId ?? '');
        $title   = (string)($entry->title ?? 'Unknown');
        $author  = (string)($entry->author->name ?? 'Unknown');

        if (!$videoId) continue;
        if (in_array($videoId, $existingIds)) { $skipped++; continue; }

        $track = [
            'id'           => 'custom-' . $videoId,
            'title'        => $title,
            'artist'       => $author,
            'category'     => $category,
            'youtube_id'   => $videoId,
            'search_query' => $title . ' ' . $author,
            'mood'         => '',
            'bpm'          => '',
            'custom'       => true,
        ];
        $music['tracks'][] = $track;
        $existingIds[] = $videoId;
        $added[] = $title;
    }

    if (!in_array('Custom', $music['categories'] ?? [])) {
        $music['categories'][] = 'Custom';
    }
    writeJson($musicFile, $music);
    echo json_encode(['ok' => true, 'added' => count($added), 'skipped' => $skipped, 'titles' => $added]);
    exit;
}

// ── Start the watcher engine (detached) ───────────────────
if ($action === 'start-watcher') {
    // Already running? (last_tick within 10s)
    $game = readJson($base . '/data/game.json');
    $lt = $game['watcher']['last_tick'] ?? null;
    if ($lt && (time() - strtotime($lt)) < 10) {
        echo json_encode(['ok' => true, 'already_running' => true]);
        exit;
    }
    // Launch via PowerShell Start-Process (silent, works from web server context)
    $watcherDir = $base . '\\watcher';
    $ps = 'powershell -NonInteractive -WindowStyle Hidden -Command "Start-Process -FilePath \\"C:\\Program Files\\nodejs\\node.exe\\" -ArgumentList \\"watcher.js\\" -WorkingDirectory \\"' . $watcherDir . '\\" -WindowStyle Hidden"';
    pclose(popen($ps, 'r'));
    echo json_encode(['ok' => true, 'started' => true]);
    exit;
}

// ── Watcher status ────────────────────────────────────────
if ($action === 'watcher-status') {
    $game = readJson($base . '/data/game.json');
    $lt = $game['watcher']['last_tick'] ?? null;
    $running = $lt ? ((time() - strtotime($lt)) < 10) : false;
    echo json_encode(['running' => $running, 'last_tick' => $lt]);
    exit;
}

// ── Get event log (raw text) ──────────────────────────────
// ── Save watcher config (ai_tool, ai_model) ────────────────
if ($action === 'save-watcher-config' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $configFile = $base . '/watcher/config.json';
    $input = json_decode(file_get_contents('php://input'), true);
    $config = readJson($configFile);
    if (!$config) {
        http_response_code(500); echo json_encode(['error' => 'Cannot read config']); exit;
    }
    if (isset($input['ai_tool'])) {
        $config['settings']['ai_tool'] = in_array($input['ai_tool'], ['claude', 'opencode']) ? $input['ai_tool'] : 'claude';
    }
    if (isset($input['ai_model'])) {
        $config['settings']['ai_model'] = trim($input['ai_model']) ?? '';
    }
    writeJson($configFile, $config);
    echo json_encode(['ok' => true, 'ai_tool' => $config['settings']['ai_tool'], 'ai_model' => $config['settings']['ai_model']]);
    exit;
}

// ── Stop the watcher engine ────────────────────────────────
if ($action === 'stop-watcher') {
    // Kill cmd window by title (covers the bat's window)
    exec('taskkill /f /fi "WINDOWTITLE eq TI-Watcher" 2>nul', $output, $rc);
    // Also kill node process by PID (in case windowsHide hid the title)
    $pidFile = $base . '/watcher/watcher.pid';
    if (file_exists($pidFile)) {
        $pid = intval(trim(file_get_contents($pidFile)));
        if ($pid > 0) exec("taskkill /PID {$pid} /F 2>nul");
        @unlink($pidFile);
    }
    echo json_encode(['ok' => true, 'killed' => true]);
    exit;
}

// ── Restart the watcher engine ─────────────────────────────
if ($action === 'restart-watcher') {
    // Kill existing instance — by window title and by PID file
    exec('taskkill /f /fi "WINDOWTITLE eq TI-Watcher" 2>nul');
    $pidFile = $base . '/watcher/watcher.pid';
    if (file_exists($pidFile)) {
        $pid = intval(trim(file_get_contents($pidFile)));
        if ($pid > 0) exec("taskkill /PID {$pid} /F 2>nul");
        @unlink($pidFile);
    }
    usleep(700000); // 0.7s — let node exit and release locks
    // Launch via PowerShell Start-Process (works from web server context without a visible window)
    $watcherJs  = $base . '\\watcher\\watcher.js';
    $watcherDir = $base . '\\watcher';
    $ps = 'powershell -NonInteractive -WindowStyle Hidden -Command "Start-Process -FilePath \\"C:\\Program Files\\nodejs\\node.exe\\" -ArgumentList \\"watcher.js\\" -WorkingDirectory \\"' . $watcherDir . '\\" -WindowStyle Hidden"';
    pclose(popen($ps, 'r'));
    echo json_encode(['ok' => true, 'restarted' => true]);
    exit;
}

// ── Get watcher config ─────────────────────────────────────
if ($action === 'get-watcher-config') {
    $configFile = $base . '/watcher/config.json';
    $config = readJson($configFile);
    if (!$config) {
        http_response_code(500); echo json_encode(['error' => 'Cannot read config']); exit;
    }
    echo json_encode([
        'ai_tool' => $config['settings']['ai_tool'] ?? 'claude',
        'ai_model' => $config['settings']['ai_model'] ?? '',
    ]);
    exit;
}

// (freesound endpoint removed — uses direct iframe embed instead)

http_response_code(400);
echo json_encode(['error' => 'Unknown action: ' . htmlspecialchars($action)]);
